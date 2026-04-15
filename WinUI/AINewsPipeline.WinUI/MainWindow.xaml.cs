using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using AINewsPipeline.WinUI.Views;

namespace AINewsPipeline.WinUI
{
    public sealed partial class MainWindow : Window
    {
        public MainWindow()
        {
            this.InitializeComponent();

            // 设置窗口大小
            this.AppWindow.Resize(new Windows.Graphics.SizeInt32(1200, 800));

            NavView.SelectedItem = NavCollect;
            ContentFrame.Navigate(typeof(CollectPage));
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
            // 状态更新功能将在后续实现
        }
    }
}
