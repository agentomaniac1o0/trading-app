ASSET_DB = {
    "Gold":            {"symbol": "GC=F",    "market": "rohstoff"},
    "Silber":          {"symbol": "SI=F",    "market": "rohstoff"},
    "Platin":          {"symbol": "PL=F",    "market": "rohstoff"},
    "Palladium":       {"symbol": "PA=F",    "market": "rohstoff"},
    "Kupfer":          {"symbol": "HG=F",    "market": "rohstoff"},
    "Öl (WTI)":        {"symbol": "CL=F",    "market": "rohstoff"},
    "Erdgas":          {"symbol": "NG=F",    "market": "rohstoff"},
    "Nasdaq 100":      {"symbol": "QQQ",   "market": "technologie"},
    "Tech-Sektor":     {"symbol": "XLK",   "market": "technologie"},
    "Halbleiter":      {"symbol": "SOXX",  "market": "technologie"},
    "ARK Innovation":  {"symbol": "ARKK",  "market": "technologie"},
    "Robotik":         {"symbol": "ROBO",  "market": "technologie"},
    "Cyber Security":  {"symbol": "HACK",  "market": "technologie"},
    "Nvidia":          {"symbol": "NVDA",   "market": "technologie"},
    "Microsoft":       {"symbol": "MSFT",   "market": "technologie"},
    "Alphabet":        {"symbol": "GOOGL",  "market": "technologie"},
    "Meta":            {"symbol": "META",   "market": "technologie"},
    "Amazon":          {"symbol": "AMZN",   "market": "technologie"},
    "Apple":           {"symbol": "AAPL",   "market": "technologie"},
    "Tesla":           {"symbol": "TSLA",   "market": "technologie"},
    "Eli Lilly":       {"symbol": "LLY",    "market": "pharma"},
    "American Tower":  {"symbol": "AMT",    "market": "technologie"},
    "Nio":             {"symbol": "NIO",    "market": "technologie"},
    "Alibaba":         {"symbol": "BABA",   "market": "technologie"},
    "Energy ETF":      {"symbol": "XLE",    "market": "rohstoff"},
    "Finance-Sektor":  {"symbol": "XLF",   "market": "forex"},
    "JPMorgan":        {"symbol": "JPM",    "market": "forex"},
    "Goldman Sachs":   {"symbol": "GS",     "market": "forex"},
    "Healthcare ETF":  {"symbol": "XLV",   "market": "technologie"},
    "China ETF":       {"symbol": "FXI",    "market": "technologie"},
    "Solar ETF":       {"symbol": "TAN",    "market": "technologie"},
    "RealEstate ETF":  {"symbol": "XLRE",   "market": "etf"},
    "Bitcoin":         {"symbol": "BTC",    "market": "crypto"},
    "Ethereum":        {"symbol": "ETH",    "market": "crypto"},
    "Solana":          {"symbol": "SOL",    "market": "crypto"},
    "XRP":             {"symbol": "XRP",    "market": "crypto"},
    "Cardano":         {"symbol": "ADA",    "market": "crypto"},
    "Dogecoin":        {"symbol": "DOGE",   "market": "crypto"},
    "Avalanche":       {"symbol": "AVAX",   "market": "crypto"},
    "Polkadot":        {"symbol": "DOT",    "market": "crypto"},
    "Chainlink":       {"symbol": "LINK",   "market": "crypto"},
    "Litecoin":        {"symbol": "LTC",    "market": "crypto"},
    "Euro/Dollar":     {"symbol": "EURUSD=X", "market": "forex"},
    "Dollar/Yen":      {"symbol": "JPY=X",    "market": "forex"},
    "Pfund/Dollar":    {"symbol": "GBPUSD=X", "market": "forex"},
}


def search_assets(query: str) -> list[dict]:
    q = query.lower().strip()
    results = []
    for name, data in ASSET_DB.items():
        sym_clean = data["symbol"].lower().replace("-", "").replace("=", "").replace("x", "")
        if q in name.lower() or q in sym_clean:
            results.append({
                "name": name,
                "symbol": data["symbol"],
                "market": data["market"],
            })
    return results[:10]
