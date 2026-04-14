using Microsoft.UI.Xaml;
using AINewsPipeline.WinUI.Services;

namespace AINewsPipeline.WinUI
{
    public partial class App : Application
    {
        public static SettingsService SettingsService { get; private set; }

        public App()
        {
            this.InitializeComponent();
            SettingsService = new SettingsService();
        }

        protected override void OnLaunched(LaunchActivatedEventArgs args)
        {
            MainWindow = new MainWindow();
            MainWindow.Activate();
        }

        public static MainWindow MainWindow { get; private set; }
    }
}