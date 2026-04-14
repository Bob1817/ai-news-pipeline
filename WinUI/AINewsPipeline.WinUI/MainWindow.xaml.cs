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
            if (StatusText != null)
            {
                StatusText.Text = status;
            }
        }
    }
}