using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using AINewsPipeline.WinUI.Views;
using System;

namespace AINewsPipeline.WinUI
{
    public sealed partial class MainWindow : Window
    {
        private TextBlock _statusText;

        public MainWindow()
        {
            this.InitializeComponent();

            // 设置窗口大小
            this.AppWindow.Resize(new Windows.Graphics.SizeInt32(1200, 800));

            NavView.SelectedItem = NavCollect;
            ContentFrame.Navigate(typeof(CollectPage));

            // 获取 StatusText 控件 - 延迟获取
            DispatcherQueue.TryEnqueue(async () =>
            {
                await Task.Delay(100);
                _statusText = (TextBlock)FindName("StatusText");
            });
        }

        private void NavView_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
        {
            if (args.SelectedItemContainer != null)
            {
                var tag = args.SelectedItemContainer.Tag?.ToString();

                if (string.IsNullOrEmpty(tag)) return;

                switch (tag)
                {
                    case "Collect":
                        ContentFrame.Navigate(typeof(CollectPage));
                        break;
                    case "Articles":
                        ContentFrame.Navigate(typeof(ArticlesPage));
                        break;
                    case "Publish":
                        ContentFrame.Navigate(typeof(PublishPage));
                        break;
                    case "Settings":
                        ContentFrame.Navigate(typeof(SettingsPage));
                        break;
                }
            }
        }

        public void UpdateStatus(string status)
        {
            if (_statusText != null)
            {
                _statusText.Text = status;
            }
        }
    }
}
