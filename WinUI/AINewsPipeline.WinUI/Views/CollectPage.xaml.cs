using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using AINewsPipeline.WinUI.Services;
using System;

namespace AINewsPipeline.WinUI.Views
{
    public sealed partial class CollectPage : Page
    {
        private PipelineService _pipelineService;

        public CollectPage()
        {
            this.InitializeComponent();
            _pipelineService = new PipelineService();
            _pipelineService.LogReceived += OnLogReceived;
            _pipelineService.TaskCompleted += OnTaskCompleted;
            CountSlider.ValueChanged += CountSlider_ValueChanged;
        }

        private void CountSlider_ValueChanged(object sender, Microsoft.UI.Xaml.Controls.Primitives.RangeBaseValueChangedEventArgs e)
        {
            CountText.Text = ((int)e.NewValue).ToString();
        }

        private async void StartButton_Click(object sender, RoutedEventArgs e)
        {
            StartButton.IsEnabled = false;
            StopButton.IsEnabled = true;
            LogPanel.Children.Clear();

            AddLog("开始执行采集流程...");

            var config = new CollectConfig
            {
                Industry = IndustryComboBox.SelectedItem?.ToString() ?? "",
                Keywords = KeywordsTextBox.Text,
                Count = (int)CountSlider.Value,
                IncludeNews = NewsSourceToggle.IsOn,
                IncludeBaidu = BaiduToggle.IsOn,
                IncludeWeibo = WeiboToggle.IsOn
            };

            await _pipelineService.RunPipelineAsync(config);
        }

        private void StopButton_Click(object sender, RoutedEventArgs e)
        {
            _pipelineService.StopPipeline();
            AddLog("已停止采集流程");
            StartButton.IsEnabled = true;
            StopButton.IsEnabled = false;
        }

        private void OnLogReceived(string message)
        {
            this.DispatcherQueue.TryEnqueue(() => AddLog(message));
        }

        private void OnTaskCompleted(bool success, string message)
        {
            this.DispatcherQueue.TryEnqueue(() =>
            {
                AddLog(success ? $"任务完成: {message}" : $"任务失败: {message}");
                StartButton.IsEnabled = true;
                StopButton.IsEnabled = false;
                
                App.MainWindow?.UpdateStatus(success ? "就绪" : "任务失败");
            });
        }

        private void AddLog(string message)
        {
            var textBlock = new TextBlock
            {
                Text = $"[{DateTime.Now:HH:mm:ss}] {message}",
                TextWrapping = TextWrapping.Wrap
            };
            LogPanel.Children.Add(textBlock);
        }
    }
}