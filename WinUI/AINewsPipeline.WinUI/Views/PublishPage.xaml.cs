using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using AINewsPipeline.WinUI.Models;
using System.Collections.Generic;
using System.Linq;

namespace AINewsPipeline.WinUI.Views
{
    public sealed partial class PublishPage : Page
    {
        private List<PlatformItem> platforms = new List<PlatformItem>();
        private List<ArticleItem> articles = new List<ArticleItem>();
        private List<PublishRecord> history = new List<PublishRecord>();

        public PublishPage()
        {
            this.InitializeComponent();
            LoadData();
        }

        private void LoadData()
        {
            platforms = new List<PlatformItem>
            {
                new PlatformItem { Id = "1", Name = "微信公众号", IsSelected = false },
                new PlatformItem { Id = "2", Name = "微博", IsSelected = false },
                new PlatformItem { Id = "3", Name = "知乎", IsSelected = false },
                new PlatformItem { Id = "4", Name = "今日头条", IsSelected = false },
                new PlatformItem { Id = "5", Name = "个人网站", IsSelected = false }
            };

            articles = new List<ArticleItem>
            {
                new ArticleItem { Id = "1", Title = "《中国科技人力资源发展研究报告》发布", IsSelected = false },
                new ArticleItem { Id = "2", Title = "科技人力资源研究：驱动创新的关键力量", IsSelected = false },
                new ArticleItem { Id = "3", Title = "厘清核心概念：科技人力资源定义再探", IsSelected = false }
            };

            history = new List<PublishRecord>
            {
                new PublishRecord
                {
                    Id = "1",
                    Title = "科技人力资源发展报告发布",
                    Platform = "微信公众号",
                    PublishedAt = "2026-04-14 10:30",
                    Status = "成功",
                    StatusBrush = new SolidColorBrush(Microsoft.UI.Colors.Green)
                },
                new PublishRecord
                {
                    Id = "2",
                    Title = "科技人力资源研究报告",
                    Platform = "微博",
                    PublishedAt = "2026-04-13 15:20",
                    Status = "成功",
                    StatusBrush = new SolidColorBrush(Microsoft.UI.Colors.Green)
                },
                new PublishRecord
                {
                    Id = "3",
                    Title = "科技人力资源定义解析",
                    Platform = "知乎",
                    PublishedAt = "2026-04-12 09:15",
                    Status = "失败",
                    StatusBrush = new SolidColorBrush(Microsoft.UI.Colors.Red)
                }
            };

            PlatformListView.ItemsSource = platforms;
            ArticlesListView.ItemsSource = articles;
            HistoryListView.ItemsSource = history;
        }

        private void PlatformCheckBox_Checked(object sender, RoutedEventArgs e)
        {
            if (sender is CheckBox checkBox && checkBox.DataContext is PlatformItem platform)
            {
                platform.IsSelected = checkBox.IsChecked ?? false;
            }
        }

        private void PlatformCheckBox_Unchecked(object sender, RoutedEventArgs e)
        {
            if (sender is CheckBox checkBox && checkBox.DataContext is PlatformItem platform)
            {
                platform.IsSelected = false;
            }
        }

        private void ArticleCheckBox_Checked(object sender, RoutedEventArgs e)
        {
            if (sender is CheckBox checkBox && checkBox.DataContext is ArticleItem article)
            {
                article.IsSelected = checkBox.IsChecked ?? false;
            }
        }

        private void ArticleCheckBox_Unchecked(object sender, RoutedEventArgs e)
        {
            if (sender is CheckBox checkBox && checkBox.DataContext is ArticleItem article)
            {
                article.IsSelected = false;
            }
        }

        private void PublishButton_Click(object sender, RoutedEventArgs e)
        {
            var selectedPlatforms = platforms.Where(p => p.IsSelected).ToList();
            var selectedArticles = articles.Where(a => a.IsSelected).ToList();

            if (selectedPlatforms.Count == 0)
            {
                ShowDialog("提示", "请至少选择一个发布平台");
                return;
            }

            if (selectedArticles.Count == 0)
            {
                ShowDialog("提示", "请至少选择一篇文章");
                return;
            }

            var dialogConfirm = new ContentDialog
            {
                Title = "确认发布",
                Content = $"即将发布 {selectedArticles.Count} 篇文章到 {selectedPlatforms.Count} 个平台",
                PrimaryButtonText = "发布",
                SecondaryButtonText = "取消"
            };
            dialogConfirm.XamlRoot = this.XamlRoot;
            dialogConfirm.PrimaryButtonClick += (s, args) =>
            {
                foreach (var article in selectedArticles)
                {
                    foreach (var platform in selectedPlatforms)
                    {
                        history.Insert(0, new PublishRecord
                        {
                            Id = GetNextRecordId().ToString(),
                            Title = article.Title,
                            Platform = platform.Name,
                            PublishedAt = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm"),
                            Status = "成功",
                            StatusBrush = new SolidColorBrush(Microsoft.UI.Colors.Green)
                        });
                    }
                }
                HistoryListView.ItemsSource = null;
                HistoryListView.ItemsSource = history;
                ShowDialog("发布成功", "文章已成功发布到所选平台");
            };
            dialogConfirm.ShowAsync();
        }

        private int GetNextRecordId()
        {
            if (history.Count == 0)
                return 1;

            var maxId = history.Select(r => int.Parse(r.Id)).Max();
            return maxId + 1;
        }

        private void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            LoadData();
        }

        private void ShowDialog(string title, string content)
        {
            var dialog = new ContentDialog
            {
                Title = title,
                Content = content,
                PrimaryButtonText = "确定"
            };
            dialog.XamlRoot = this.XamlRoot;
            dialog.ShowAsync();
        }
    }
}