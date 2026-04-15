using Microsoft.UI;
using Microsoft.UI.Xaml.Media;

namespace AINewsPipeline.WinUI.Models
{
    public class ArticleItem : BindableBase
    {
        private string _id;
        private string _title;
        private string _content;
        private string _createdAt;
        private string _status;
        private SolidColorBrush _statusBrush;
        private bool _isSelected;

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

        public string Content
        {
            get => _content;
            set => SetProperty(ref _content, value);
        }

        public string CreatedAt
        {
            get => _createdAt;
            set => SetProperty(ref _createdAt, value);
        }

        public string Status
        {
            get => _status;
            set => SetProperty(ref _status, value);
        }

        public SolidColorBrush StatusBrush
        {
            get => _statusBrush;
            set => SetProperty(ref _statusBrush, value);
        }

        public bool IsSelected
        {
            get => _isSelected;
            set => SetProperty(ref _isSelected, value);
        }
    }
}