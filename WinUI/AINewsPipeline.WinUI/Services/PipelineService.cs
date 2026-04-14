using Newtonsoft.Json;
using System;
using System.Diagnostics;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

namespace AINewsPipeline.WinUI.Services
{
    public class PipelineService
    {
        public event Action<string> LogReceived;
        public event Action<bool, string> TaskCompleted;

        private HttpClient _httpClient;
        private bool _isRunning;

        public PipelineService()
        {
            _httpClient = new HttpClient();
            _httpClient.Timeout = TimeSpan.FromMinutes(30);
        }

        public async Task RunPipelineAsync(CollectConfig config)
        {
            _isRunning = true;

            try
            {
                OnLogReceived("正在启动Python后端服务...");
                
                var pythonProcess = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = "main.py --mode=api",
                        WorkingDirectory = "../../",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true
                    }
                };

                pythonProcess.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        OnLogReceived(e.Data);
                    }
                };

                pythonProcess.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        OnLogReceived($"错误: {e.Data}");
                    }
                };

                pythonProcess.Start();
                pythonProcess.BeginOutputReadLine();
                pythonProcess.BeginErrorReadLine();

                await Task.Delay(3000);

                OnLogReceived("连接到后端服务...");

                var requestData = new
                {
                    industry = config.Industry,
                    keywords = config.Keywords,
                    count = config.Count,
                    sources = new
                    {
                        news = config.IncludeNews,
                        baidu = config.IncludeBaidu,
                        weibo = config.IncludeWeibo
                    }
                };

                var jsonContent = JsonConvert.SerializeObject(requestData);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                try
                {
                    var response = await _httpClient.PostAsync("http://localhost:5000/run-pipeline", content);
                    response.EnsureSuccessStatusCode();

                    var responseJson = await response.Content.ReadAsStringAsync();
                    var result = JsonConvert.DeserializeObject<PipelineResult>(responseJson);

                    OnLogReceived($"新闻采集: {result.NewsCount}条");
                    OnLogReceived($"主题提炼: {result.ThemeCount}个");
                    OnLogReceived($"文章生成: {result.ArticleCount}篇");

                    OnTaskCompleted(true, "流程执行完成");
                }
                catch (HttpRequestException ex)
                {
                    OnLogReceived($"API请求失败: {ex.Message}");
                    OnTaskCompleted(false, ex.Message);
                }

                pythonProcess.Kill();
            }
            catch (Exception ex)
            {
                OnLogReceived($"执行失败: {ex.Message}");
                OnTaskCompleted(false, ex.Message);
            }
            finally
            {
                _isRunning = false;
            }
        }

        public void StopPipeline()
        {
            _isRunning = false;
        }

        protected virtual void OnLogReceived(string message)
        {
            LogReceived?.Invoke(message);
        }

        protected virtual void OnTaskCompleted(bool success, string message)
        {
            TaskCompleted?.Invoke(success, message);
        }
    }

    public class PipelineResult
    {
        public int NewsCount { get; set; }
        public int ThemeCount { get; set; }
        public int ArticleCount { get; set; }
    }
}