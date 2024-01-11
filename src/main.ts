import yahooFinance from "yahoo-finance2";
import { ChartResultArrayQuote } from "yahoo-finance2/dist/esm/src/modules/chart";

enum Decision {
  BUY,
  SELL,
  HOLD,
}

class Config {
  trendLength: number;
  buyThreshold: number;
  sellThreshold: number;

  constructor() {
    this.trendLength = 5;
    this.buyThreshold = 0.00001;
    this.sellThreshold = -0.00002;
  }

  clone() {
    const config = new Config();
    config.trendLength = this.trendLength;
    config.buyThreshold = this.buyThreshold;
    config.sellThreshold = this.sellThreshold;
    return config;
  }

  mutate() {
    const config = this.clone();

    let rand = Math.random();

    if (rand < 0.25) config.trendLength += 1;
    else if (rand < 0.5 && config.trendLength > 1) config.trendLength -= 1;
    else if (rand < 0.75) config.buyThreshold += 0.0000025;
    else config.buyThreshold -= 0.0000025;

    return config;
  }
}

const config: Config = new Config();

const decide = (
  quote: ChartResultArrayQuote,
  quotes: ChartResultArrayQuote[],
  config: Config
): Decision => {
  // Calculate trend (avg change of recent quotes)
  let trend = 0;
  for (let i = 1; i <= config.trendLength && i < quotes.length; i++) {
    const prev = quotes[quotes.length - i];
    if (prev.close && prev.open) trend += prev.close / prev.open;
  }
  trend /= config.trendLength;
  trend = 1 - trend;

  // console.log(`Trend: ${trend}`);

  // We started with 0.00001 for buy and 0.00002 for sell

  if (trend > config.buyThreshold) return Decision.BUY;
  else if (trend < config.sellThreshold) return Decision.SELL;
  else return Decision.HOLD;
};

const testMultiDay = async (
  quotes: ChartResultArrayQuote[],
  config: Config
): Promise<number> => {
  const startingMoney = quotes[0].open!;

  let money = startingMoney,
    shares = 0;
  for (let i = 0; i < quotes.length; i++) {
    // Find start and end dates
    const start = new Date();
    start.setDate(start.getDate() - quotes.length + i);

    // Skip weekends
    if (start.getDay() === 0 || start.getDay() === 6) {
      continue;
    }

    const end = new Date();
    end.setDate(start.getDate() + 1);

    try {
      const quote = quotes[i];

      const decision = decide(quote, quotes.slice(0, i), config);

      // console.log(`${quote.date}: ${Decision[decision]}`);

      // Act on decision
      if (decision === Decision.BUY) {
        shares += money / quote.open!;
        money = 0;
      } else if (decision === Decision.SELL) {
        money += shares * quote.close!;
        shares = 0;
      }
    } catch (e) {
      // console.log(`Error on ${start.toDateString()}`);
    }
  }

  // Find ending share price
  const finalPrice = quotes[quotes.length - 1].open;

  // Calculate net worth
  const netWorth = shares * finalPrice! + money;

  // Calculate % profit
  const profitPercent = (netWorth - startingMoney) / startingMoney;

  return profitPercent;
};

const main = async () => {
  let bestConfig: Config | null = null,
    bestProfit: number | null = null;

  // Config
  const days = 365 * 3,
    trials = 5000;
  const symbols = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "NVDA",
    "GOOG",
    "LLY",
    "JPM",
    "UNH",
    "AVGO",
    "V",
    "XOM",
    "JNJ",
    "FXAIX",
  ];

  // Find start and end dates
  const start = new Date();
  start.setDate(start.getDate() - days);
  const end = new Date();

  // Find chart data for entire period
  const quoteData: ChartResultArrayQuote[][] = [];
  let fxaix: ChartResultArrayQuote[] | null = null;
  for (const symbol of symbols) {
    const { quotes } = await yahooFinance.chart(symbol, {
      period1: start.toDateString(),
      period2: end.toDateString(),
      interval: "1d",
    });
    quoteData.push(quotes);

    if (symbol === "FXAIX") fxaix = quotes;
  }

  let config = new Config();
  for (let i = 0; i < trials; i++) {
    console.log(`Testing config ${i}...`);
    console.log(config);

    // Test config
    let profit = 0;
    for (const quotes of quoteData) {
      profit += await testMultiDay(quotes, config);
    }
    profit /= quoteData.length;

    if (!bestProfit || profit > bestProfit) {
      bestProfit = profit;
      bestConfig = config;
    }

    console.log(`Profit: ${profit} vs. ${bestProfit}`);

    config = config.mutate();
  }

  console.log("Done!");
  console.log("-------------------------");
  console.log("Best config:");
  console.log(bestConfig ?? "null");

  // Compare to FXAIX change
  if (fxaix) {
    const fxaixChange =
      ((fxaix as any)[0] as ChartResultArrayQuote).close! /
      ((fxaix as any)[fxaix.length - 1] as ChartResultArrayQuote).open!;
    console.log(`FXAIX change: ${fxaixChange}`);
  }

  console.log("Best profit:");
  console.log(bestProfit);
};

main();
