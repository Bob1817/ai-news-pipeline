using System;
using System.IO;
using Newtonsoft.Json;
using Windows.Storage;

namespace AINewsPipeline.WinUI.Services
{
    public class SettingsService
    {
        private const string SettingsFileName = "settings.json";
        private string _settingsPath;

        public event EventHandler<SettingsChangedEventArgs> SettingsChanged;

        public SettingsService()
        {
            _settingsPath = Path.Combine(ApplicationData.Current.LocalFolder.Path, SettingsFileName);
            LoadSettings();
        }

        private SettingsData _settings;

        public SettingsData Settings
        {
            get => _settings ?? new SettingsData();
            private set
            {
                _settings = value;
                SaveSettings();
            }
        }

        public void LoadSettings()
        {
            try
            {
                if (File.Exists(_settingsPath))
                {
                    var json = File.ReadAllText(_settingsPath);
                    Settings = JsonConvert.DeserializeObject<SettingsData>(json) ?? new SettingsData();
                }
                else
                {
                    Settings = new SettingsData();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加载设置失败：{ex.Message}");
                Settings = new SettingsData();
            }
        }

        public void SaveSettings()
        {
            try
            {
                var json = JsonConvert.SerializeObject(Settings, Formatting.Indented);
                File.WriteAllText(_settingsPath, json);
                SettingsChanged?.Invoke(this, new SettingsChangedEventArgs(Settings));
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"保存设置失败：{ex.Message}");
            }
        }

        public void ResetToDefaults()
        {
            Settings = new SettingsData();
            SaveSettings();
        }
    }

    public class SettingsChangedEventArgs : EventArgs
    {
        public SettingsData Settings { get; }

        public SettingsChangedEventArgs(SettingsData settings)
        {
            Settings = settings;
        }
    }

    public class SettingsData
    {
        // LLM 配置
        public string LlmProvider { get; set; } = "Ollama";
        public string ModelName { get; set; } = "llama3";
        public string ApiKey { get; set; } = "";
        public string ApiUrl { get; set; } = "http://localhost:11434";
        public double Temperature { get; set; } = 0.7;

        // 文章参数
        public int ArticleLength { get; set; } = 1000;
        public string Style { get; set; } = "正式";
        public bool AutoImage { get; set; } = true;
        public bool SeoOptimization { get; set; } = true;

        // 发布设置
        public bool AutoPublish { get; set; } = false;
        public int PublishInterval { get; set; } = 60;
        public bool AutoImageForWeChat { get; set; } = true;
        public bool AutoImageForWeibo { get; set; } = false;
        public bool AutoImageForZhihu { get; set; } = false;

        // 采集设置
        public bool AutoCollect { get; set; } = false;
        public int CollectInterval { get; set; } = 30;
        public int MaxCollectCount { get; set; } = 20;
    }
}
