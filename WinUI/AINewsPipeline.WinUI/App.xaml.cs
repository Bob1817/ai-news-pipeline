using Microsoft.UI.Xaml;

namespace AINewsPipeline.WinUI
{
    public partial class App : Application
    {
        public App()
        {
            this.InitializeComponent();
        }

        protected override void OnLaunched(LaunchActivatedEventArgs args)
        {
            MainWindow = new MainWindow();
            MainWindow.Activate();
        }

        public static MainWindow MainWindow { get; private set; }
    }
}