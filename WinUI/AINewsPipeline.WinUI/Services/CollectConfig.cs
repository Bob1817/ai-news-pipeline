namespace AINewsPipeline.WinUI.Services
{
    public class CollectConfig
    {
        public string Industry { get; set; }
        public string Keywords { get; set; }
        public int Count { get; set; }
        public bool IncludeNews { get; set; }
        public bool IncludeBaidu { get; set; }
        public bool IncludeWeibo { get; set; }
    }
}