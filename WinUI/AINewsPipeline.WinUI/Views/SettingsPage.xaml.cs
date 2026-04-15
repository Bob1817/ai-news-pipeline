using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Windows.Storage;

namespace AINewsPipeline.WinUI.Views
{
    public sealed partial class SettingsPage : Page
    {
        public SettingsPage()
        {
            this.InitializeComponent();
            WireUpSliders();
            LoadSettings();
        }

        private void WireUpSliders()
        {
            TemperatureSlider.ValueChanged += (s, e) => TemperatureText.Text = e.NewValue.ToString("0.00");
            ArticleLengthSlider.ValueChanged += (s, e) => ArticleLengthText.Text = ((int)e.NewValue).ToString();
            IntervalSlider.ValueChanged += (s, e) => IntervalText.Text = ((int)e.NewValue).ToString();
            CollectIntervalSlider.ValueChanged += (s, e) => CollectIntervalText.Text = ((int)e.NewValue).ToString();
            MaxCountSlider.ValueChanged += (s, e) => MaxCountText.Text = ((int)e.NewValue).ToString();

            ShowKeyCheckBox.Checked += (s, e) => ApiKeyBox.PasswordRevealMode = PasswordRevealMode.Visible;
            ShowKeyCheckBox.Unchecked += (s, e) => ApiKeyBox.PasswordRevealMode = PasswordRevealMode.Hidden;
        }

        private void SaveButton_Click(object sender, RoutedEventArgs e)
        {
            var settings = new SettingsData
            {
                LlmProvider = OllamaRadio.IsChecked == true ? "Ollama" : "OpenAI",
                ModelName = ModelNameTextBox.Text,
                ApiKey = ApiKeyBox.Password,
                ApiUrl = ApiUrlTextBox.Text,
                Temperature = TemperatureSlider.Value,
                ArticleLength = (int)ArticleLengthSlider.Value,
                Style = StyleComboBox.SelectedItem?.ToString() ?? "正式",
                AutoImage = AutoImageToggle.IsOn,
                SeoOptimization = SeoToggle.IsOn,
                PublishInterval = (int)IntervalSlider.Value,
                AutoPublish = AutoPublishToggle.IsOn,
                CollectInterval = (int)CollectIntervalSlider.Value,
                MaxCollectCount = (int)MaxCountSlider.Value,
                AutoCollect = AutoCollectToggle.IsOn
            };

            SaveSettings(settings);

            var dialog = new ContentDialog
            {
                Title = "保存成功",
                Content = "设置已保存",
                PrimaryButtonText = "确定"
            };
            dialog.XamlRoot = this.XamlRoot;
            dialog.ShowAsync();
        }

        private void ResetButton_Click(object sender, RoutedEventArgs e)
        {
            OllamaRadio.IsChecked = true;
            OpenAIRadio.IsChecked = false;
            ModelNameTextBox.Text = "";
            ApiKeyBox.Password = "";
            ApiUrlTextBox.Text = "";
            TemperatureSlider.Value = 0.7;
            ArticleLengthSlider.Value = 1000;
            StyleComboBox.SelectedIndex = 0;
            AutoImageToggle.IsOn = true;
            SeoToggle.IsOn = true;
            WeChatCheckBox.IsChecked = true;
            WeiboCheckBox.IsChecked = false;
            ZhihuCheckBox.IsChecked = false;
            IntervalSlider.Value = 60;
            AutoPublishToggle.IsOn = false;
            CollectIntervalSlider.Value = 30;
            MaxCountSlider.Value = 20;
            AutoCollectToggle.IsOn = false;
        }

        private void SaveSettings(SettingsData settings)
        {
            try
            {
                var localFolder = ApplicationData.Current.LocalFolder;
                var settingsPath = Path.Combine(localFolder.Path, "settings.json");
                var json = JsonConvert.SerializeObject(settings, Formatting.Indented);
                File.WriteAllText(settingsPath, json);
            }
            catch (System.Exception ex)
            {
                var dialog = new ContentDialog
                {
                    Title = "保存失败",
                    Content = $"保存设置时出错：{ex.Message}",
                    PrimaryButtonText = "确定"
                };
                dialog.XamlRoot = this.XamlRoot;
                dialog.ShowAsync();
            }
        }

        private void LoadSettings()
        {
            try
            {
                var localFolder = ApplicationData.Current.LocalFolder;
                var settingsPath = Path.Combine(localFolder.Path, "settings.json");
                if (File.Exists(settingsPath))
                {
                    var json = File.ReadAllText(settingsPath);
                    var settings = JsonConvert.DeserializeObject<SettingsData>(json);
                    if (settings != null)
                    {
                        LoadSettingsFromData(settings);
                    }
                }
            }
            catch { }
        }

        private void LoadSettingsFromData(SettingsData settings)
        {
            if (settings.LlmProvider == "OpenAI")
            {
                OpenAIRadio.IsChecked = true;
                OllamaRadio.IsChecked = false;
            }
            else
            {
                OllamaRadio.IsChecked = true;
                OpenAIRadio.IsChecked = false;
            }

            ModelNameTextBox.Text = settings.ModelName;
            ApiKeyBox.Password = settings.ApiKey;
            ApiUrlTextBox.Text = settings.ApiUrl;
            TemperatureSlider.Value = settings.Temperature;
            TemperatureText.Text = settings.Temperature.ToString("0.00");
            ArticleLengthSlider.Value = settings.ArticleLength;
            ArticleLengthText.Text = settings.ArticleLength.ToString();
            StyleComboBox.SelectedIndex = System.Array.IndexOf(new[] { "正式", "轻松", "专业", "幽默" }, settings.Style) >= 0
                ? System.Array.IndexOf(new[] { "正式", "轻松", "专业", "幽默" }, settings.Style)
                : 0;
            AutoImageToggle.IsOn = settings.AutoImage;
            SeoToggle.IsOn = settings.SeoOptimization;
            IntervalSlider.Value = settings.PublishInterval;
            IntervalText.Text = settings.PublishInterval.ToString();
            AutoPublishToggle.IsOn = settings.AutoPublish;
            CollectIntervalSlider.Value = settings.CollectInterval;
            CollectIntervalText.Text = settings.CollectInterval.ToString();
            MaxCountSlider.Value = settings.MaxCollectCount;
            MaxCountText.Text = settings.MaxCollectCount.ToString();
            AutoCollectToggle.IsOn = settings.AutoCollect;
        }
    }

    public class SettingsData
    {
        public string LlmProvider { get; set; }
        public string ModelName { get; set; }
        public string ApiKey { get; set; }
        public string ApiUrl { get; set; }
        public double Temperature { get; set; }
        public int ArticleLength { get; set; }
        public string Style { get; set; }
        public bool AutoImage { get; set; }
        public bool SeoOptimization { get; set; }
        public int PublishInterval { get; set; }
        public bool AutoPublish { get; set; }
        public int CollectInterval { get; set; }
        public int MaxCollectCount { get; set; }
        public bool AutoCollect { get; set; }
    }
}