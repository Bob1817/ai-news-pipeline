using Newtonsoft.Json;
using System;
using System.Diagnostics;
using System.IO;
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

            Process pythonProcess = null;

            try
            {
                OnLogReceived("正在启动 Python 后端服务...");

                var pythonPath = GetPythonExecutable();
                if (string.IsNullOrEmpty(pythonPath))
                {
                    OnLogReceived("错误：未找到 Python 可执行文件，请确保已安装 Python");
                    OnTaskCompleted(false, "未找到 Python");
                    return;
                }

                OnLogReceived($"使用 Python: {pythonPath}");

                pythonProcess = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = pythonPath,
                        Arguments = "main.py --mode=api",
                        WorkingDirectory = "../../",
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true,
                        EnvironmentVariables = { ["PYTHONIOENCODING"] = "utf-8" }
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
                        OnLogReceived($"错误：{e.Data}");
                    }
                };

                pythonProcess.Start();
                pythonProcess.BeginOutputReadLine();
                pythonProcess.BeginErrorReadLine();

                OnLogReceived("等待 Python 服务启动...");
                await Task.Delay(5000);

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

                    OnLogReceived($"新闻采集：{result.NewsCount}条");
                    OnLogReceived($"主题提炼：{result.ThemeCount}个");
                    OnLogReceived($"文章生成：{result.ArticleCount}篇");

                    OnTaskCompleted(true, "流程执行完成");
                }
                catch (HttpRequestException ex)
                {
                    OnLogReceived($"API 请求失败：{ex.Message}");
                    OnLogReceived("提示：请确保 Python 后端服务正在运行 (python main.py web --port 5000)");
                    OnTaskCompleted(false, ex.Message);
                }
                finally
                {
                    if (pythonProcess != null && !pythonProcess.HasExited)
                    {
                        try
                        {
                            pythonProcess.Kill();
                        }
                        catch { }
                    }
                }
            }
            catch (Exception ex)
            {
                OnLogReceived($"执行失败：{ex.Message}");
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

        private string GetPythonExecutable()
        {
            var possiblePaths = new[]
            {
                "python",
                "python3",
                Path.Combine("../../", "venv", "Scripts", "python.exe"),
                Path.Combine("../../", "venv", "bin", "python"),
                Path.Combine(AppContext.BaseDirectory, "venv", "Scripts", "python.exe"),
                Path.Combine(AppContext.BaseDirectory, "venv", "bin", "python")
            };

            foreach (var path in possiblePaths)
            {
                try
                {
                    if (File.Exists(path))
                    {
                        return path;
                    }

                    var startInfo = new ProcessStartInfo
                    {
                        FileName = path,
                        ArgumentList = { "--version" },
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        CreateNoWindow = true
                    };

                    using var process = Process.Start(startInfo);
                    process.WaitForExit(2000);
                    if (process.ExitCode == 0)
                    {
                        return path;
                    }
                }
                catch { }
            }

            return null;
        }
    }

    public class PipelineResult
    {
        public int NewsCount { get; set; }
        public int ThemeCount { get; set; }
        public int ArticleCount { get; set; }
    }
}
