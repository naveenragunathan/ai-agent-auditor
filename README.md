# AI Website Audit Agent Suite

A comprehensive AI-powered website audit application that analyzes websites across multiple dimensions using specialized AI agents.

## Features

- **Multi-Agent Analysis**: 6 specialized AI agents analyze different aspects of your website
- **Real-time Scraping**: Extracts website content and creator profile data
- **Comprehensive Scoring**: Overall score (0-100) with category breakdowns
- **Actionable Insights**: Critical issues, quick wins, and detailed recommendations
- **Modern UI**: Clean, responsive interface with real-time progress updates
- **Data Storage**: Saves audit results for future reference

## AI Agents

1. **Business & Profile Agent** - Analyzes business model, positioning, and target audience
2. **Style & Brand Alignment Agent** - Checks brand consistency across platforms
3. **Hero Section Agent** - Evaluates headline clarity and CTA effectiveness
4. **Problem Definition Agent** - Assesses problem articulation and solution fit
5. **Copy & SEO Agent** - Reviews content quality, readability, and SEO optimization
6. **Conversion Barrier Agent** - Identifies obstacles to user conversion

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   
   Required:
   - `MISTRAL_API_KEY`: Your Mistral AI API key
   
   Optional:
   - `TWITTER_BEARER_TOKEN`: For enhanced Twitter profile analysis
   - `SUPABASE_URL` & `SUPABASE_KEY`: For cloud database storage

3. **Install Playwright** (for advanced scraping)
   ```bash
   playwright install
   ```

## Usage

1. **Start the Server**
   ```bash
   python main.py
   ```

2. **Access the Application**
   Open your browser to `http://localhost:8000`

3. **Run an Audit**
   - Enter a website URL (required)
   - Optionally add creator social profile URL
   - Optionally provide email to save results
   - Click "Run AI Audit"

## API Endpoints

- `GET /` - Main UI interface
- `POST /audit` - Run website audit
- `GET /health` - Health check

### Audit Request Format
```json
{
  "website_url": "https://example.com",
  "creator_profile": "https://twitter.com/username",
  "email": "user@example.com"
}
```

### Audit Response Format
```json
{
  "overall_score": 78,
  "category_scores": {
    "business": 85,
    "style": 72,
    "hero": 80,
    "problem": 75,
    "seo": 70,
    "conversion": 68
  },
  "critical_issues": [
    "Unclear value proposition in hero section",
    "Missing trust signals",
    "Weak call-to-action placement"
  ],
  "quick_wins": [
    "Add testimonials to homepage",
    "Optimize meta descriptions",
    "Improve CTA button contrast"
  ],
  "recommendations": [
    "Clarify your unique value proposition",
    "Add social proof elements",
    "Optimize page loading speed"
  ],
  "summary": "Good foundation with room for conversion optimization",
  "detailed_analysis": { ... }
}
```

## Architecture

```
agent-audit/
├── main.py                 # FastAPI application entry point
├── agents/
│   └── audit_agents.py     # AI agent implementations
├── scrapers/
│   ├── website_scraper.py  # Website content extraction
│   └── profile_scraper.py  # Social profile scraping
├── database/
│   └── db_manager.py       # Data storage management
├── static/
│   ├── index.html          # Frontend UI
│   └── script.js           # Frontend JavaScript
├── data/                   # Local data storage
├── requirements.txt        # Python dependencies
└── .env.example           # Environment variables template
```

## Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **AI**: LangChain + Mistral AI
- **Scraping**: aiohttp, BeautifulSoup, Playwright
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Storage**: JSON files (easily replaceable with Supabase/PostgreSQL)

## Customization

### Adding New Agents
1. Create new agent prompt in `agents/audit_agents.py`
2. Add agent to the `_initialize_agents()` method
3. Include in `run_all_agents()` execution
4. Update frontend to display new category

### Changing AI Model
Update the model in `agents/audit_agents.py`:
```python
self.llm = ChatMistralAI(
    model="mistral-large",  # Change model here
    temperature=0.1,
    mistral_api_key=os.getenv("MISTRAL_API_KEY")
)
```

### Database Integration
Replace `DatabaseManager` in `database/db_manager.py` with your preferred database solution (Supabase, PostgreSQL, etc.).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please open a GitHub issue or contact the development team.
