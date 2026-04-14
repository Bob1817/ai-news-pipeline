using AINewsPipeline.WinUI.Models;
using Windows.UI;

namespace AINewsPipeline.WinUI.Models
{
    public class PublishRecord : BindableBase
    {
        private string _id;
        private string _title;
        private string _platform;
        private string _publishedAt;
        private string _status;
        private Color _statusColor;

        public string Id
        {
            get => _id;
            set => SetProperty(ref _id, value);
        }

        public string Title
        {
            get => _title;
            set => SetProperty(ref _title, value);
        }

        public string Platform
        {
            get => _platform;
            set => SetProperty(ref _platform, value);
        }

        public string PublishedAt
        {
            get => _publishedAt;
            set => SetProperty(ref _publishedAt, value);
        }

        public string Status
        {
            get => _status;
            set => SetProperty(ref _status, value);
        }

        public Color StatusColor
        {
            get => _statusColor;
            set => SetProperty(ref _statusColor, value);
        }
    }
}