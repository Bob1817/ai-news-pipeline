using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using AINewsPipeline.WinUI.Models;
using System.Collections.Generic;
using System.Linq;

namespace AINewsPipeline.WinUI.Views
{
    public sealed partial class ArticlesPage : Page
    {
        private List<ArticleItem> articles = new List<ArticleItem>();

        public ArticlesPage()
        {
            this.InitializeComponent();
            LoadArticles();
        }

        private void LoadArticles()
        {
            articles = new List<ArticleItem>
            {
                new ArticleItem
                {
                    Id = "1",
                    Title = "《中国科技人力资源发展研究报告》发布：规模持续扩大",
                    Content = "近年来，我国科技人力资源规模持续扩大，成为推动创新发展的重要力量。报告显示，我国科技人力资源总量已突破1亿人，为经济高质量发展提供了坚实支撑。科技人力资源作为国家战略资源，其规模和质量直接影响着国家创新能力和国际竞争力。",
                    CreatedAt = "2026-04-14 10:30",
                    Status = "已发布",
                    StatusBrush = new SolidColorBrush(Microsoft.UI.Colors.Green)
                },
                new ArticleItem
                {
                    Id = "2",
                    Title = "科技人力资源研究：驱动创新的关键力量",
                    Content = "科技人力资源是创新驱动发展的核心要素。随着数字化转型加速，科技人才的需求持续增长。企业和政府都在加大对科技人才的培养和引进力度，以应对日益激烈的国际竞争。",
                    CreatedAt = "2026-04-14 09:15",
                    Status = "已生成",
                    StatusBrush = new SolidColorBrush(Microsoft.UI.Colors.Blue)
                },
                new ArticleItem
                {
                    Id = "3",
                    Title = "厘清核心概念：科技人力资源定义再探与趋势展望",
                    Content = "科技人力资源的定义随着时代发展不断演变。从传统的研发人员到现代的数字化人才，科技人力资源的范畴在不断扩展。准确理解这一概念，对于制定人才战略具有重要意义。",
                    CreatedAt = "2026-04-13 16:45",
                    Status = "待审核",
                    StatusBrush = new SolidColorBrush(Microsoft.UI.Colors.Orange)
                }
            };

            ArticlesListView.ItemsSource = articles;
        }

        private void SearchButton_Click(object sender, RoutedEventArgs e)
        {
            var keyword = SearchBox.Text.ToLower();
            var status = StatusComboBox.SelectedItem?.ToString() ?? "全部";

            var filtered = articles.Where(a => 
                (string.IsNullOrEmpty(keyword) || a.Title.ToLower().Contains(keyword)) &&
                (status == "全部" || a.Status == status)
            ).ToList();

            ArticlesListView.ItemsSource = filtered;
        }

        private void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            SearchBox.Text = "";
            StatusComboBox.SelectedIndex = 0;
            LoadArticles();
        }

        private void ArticlesListView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var selected = ArticlesListView.SelectedItem as ArticleItem;
            if (selected != null)
            {
                ContentPreview.Text = selected.Content;
                EditButton.IsEnabled = true;
                PreviewButton.IsEnabled = true;
                ExportButton.IsEnabled = true;
                DeleteButton.IsEnabled = true;
            }
            else
            {
                ContentPreview.Text = "";
                EditButton.IsEnabled = false;
                PreviewButton.IsEnabled = false;
                ExportButton.IsEnabled = false;
                DeleteButton.IsEnabled = false;
            }
        }

        private void EditButton_Click(object sender, RoutedEventArgs e)
        {
            var selected = ArticlesListView.SelectedItem as ArticleItem;
            if (selected != null)
            {
                var dialog = new ContentDialog
                {
                    Title = "编辑文章",
                    Content = new EditArticleControl(selected),
                    PrimaryButtonText = "保存",
                    SecondaryButtonText = "取消"
                };
                dialog.XamlRoot = this.XamlRoot;
                dialog.ShowAsync();
            }
        }

        private void PreviewButton_Click(object sender, RoutedEventArgs e)
        {
            var selected = ArticlesListView.SelectedItem as ArticleItem;
            if (selected != null)
            {
                var dialog = new ContentDialog
                {
                    Title = "预览文章",
                    Content = new TextBlock { Text = selected.Content, TextWrapping = TextWrapping.Wrap, Padding = new Thickness(12) },
                    PrimaryButtonText = "关闭"
                };
                dialog.XamlRoot = this.XamlRoot;
                dialog.ShowAsync();
            }
        }

        private void ExportButton_Click(object sender, RoutedEventArgs e)
        {
            var selected = ArticlesListView.SelectedItem as ArticleItem;
            if (selected != null)
            {
                ShowDialog("导出成功", $"文章已导出到: data/export/{selected.Id}_{selected.Title}.md");
            }
        }

        private void DeleteButton_Click(object sender, RoutedEventArgs e)
        {
            var selected = ArticlesListView.SelectedItem as ArticleItem;
            if (selected != null)
            {
                var dialog = new ContentDialog
                {
                    Title = "确认删除",
                    Content = $"确定要删除文章「{selected.Title}」吗？",
                    PrimaryButtonText = "删除",
                    SecondaryButtonText = "取消"
                };
                dialog.XamlRoot = this.XamlRoot;
                dialog.PrimaryButtonClick += (s, args) =>
                {
                    articles.Remove(selected);
                    ArticlesListView.ItemsSource = null;
                    ArticlesListView.ItemsSource = articles;
                    ContentPreview.Text = "";
                };
                dialog.ShowAsync();
            }
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

        public sealed class EditArticleControl : UserControl
        {
            public EditArticleControl(ArticleItem article)
            {
                var panel = new StackPanel();
                panel.Orientation = Orientation.Vertical;
                panel.Spacing = 12;

                var titlePanel = new StackPanel();
                titlePanel.Orientation = Orientation.Vertical;
                titlePanel.Children.Add(new TextBlock { Text = "标题", FontWeight = new Windows.UI.Text.FontWeight { Weight = 600 }, Margin = new Thickness(0, 0, 0, 4) });
                var titleBox = new TextBox { Text = article.Title, Margin = new Thickness(0, 0, 0, 12) };
                titlePanel.Children.Add(titleBox);

                var contentPanel = new StackPanel();
                contentPanel.Orientation = Orientation.Vertical;
                contentPanel.Children.Add(new TextBlock { Text = "内容", FontWeight = new Windows.UI.Text.FontWeight { Weight = 600 }, Margin = new Thickness(0, 0, 0, 4) });
                var contentBox = new TextBox { Text = article.Content, AcceptsReturn = true, TextWrapping = TextWrapping.Wrap, Height = 200, Margin = new Thickness(0, 0, 0, 12) };
                contentPanel.Children.Add(contentBox);

                panel.Children.Add(titlePanel);
                panel.Children.Add(contentPanel);
                this.Content = panel;
            }
        }
    }
}