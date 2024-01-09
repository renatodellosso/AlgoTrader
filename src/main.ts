import yahooFinance from "yahoo-finance2";
import { ChartResultArrayQuote } from "yahoo-finance2/dist/esm/src/modules/chart";

enum Decision {
  BUY,
  SELL,
  HOLD,
}

class Config {
  trendLength: number;
  interval: string;
  buyThreshold: number;
  sellThreshold: number;

  constructor() {
    this.trendLength = 5;
    this.interval = "5m";
    this.buyThreshold = 0.00001;
    this.sellThreshold = -0.00002;
  }

  clone() {
    const config = new Config();
    config.trendLength = this.trendLength;
    config.interval = this.interval;
    config.buyThreshold = this.buyThreshold;
    config.sellThreshold = this.sellThreshold;
    return config;
  }

  mutate() {
    const config = this.clone();

    let rand = Math.random();

    if (rand < 0.2) config.trendLength += 1;
    else if (rand < 0.4) config.trendLength -= 1;
    else if (rand < 0.6) config.buyThreshold += 0.00001;
    else if (rand < 0.8) config.buyThreshold -= 0.00001;
    else {
      // Mutate interval
      rand = Math.random();
      if (rand < 0.25) config.interval = "1m";
      else if (rand < 0.5) config.interval = "5m";
      else if (rand < 0.75) config.interval = "15m";
      else config.interval = "30m";
    }

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

  // We started with 0.00001 for buy and 0.00002 for sell

  if (trend > config.buyThreshold) return Decision.BUY;
  else if (trend < config.sellThreshold) return Decision.SELL;
  else return Decision.HOLD;
};

const testSingleDay = async (
  symbol: string,
  money: number,
  start: Date,
  end: Date,
  config: Config
): Promise<number> => {
  // console.log(
  //   `Testing ${symbol} from ${start.toString()} to ${end.toString()}...`
  // );

  const { quotes } = await yahooFinance.chart(symbol, {
    period1: start.toDateString(),
    period2: end.toDateString(),
    interval: config.interval as any,
  });

  const startingMoney = money;
  let shares = 0;

  for (let i = 0; i < quotes.length; i++) {
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
  }

  // Print results

  // console.log(`Date: ${start.toDateString()} - ${end.toDateString()}`);
  // console.log(`Starting money: $${startingMoney}`);
  // console.log(`Shares: ${shares}`);
  // console.log(`Money: $${money}`);

  const netWorth = shares * quotes[quotes.length - 1].close! + money;
  // console.log(`Total: $${money + shares * quotes[quotes.length - 1].close!}`);

  // const profit = netWorth - startingMoney;
  // console.log(
  //   `Profit: $${profit} - ${
  //     Math.round((profit / startingMoney) * 10000) / 100
  //   }%`
  // );

  return netWorth;
};

const testMultiDay = async (
  symbol: string,
  days: number,
  config: Config
): Promise<number> => {
  const start = new Date();
  start.setDate(start.getDate() - days);

  // Find chart data for entire period
  const { quotes } = await yahooFinance.chart(symbol, {
    period1: start.toDateString(),
    interval: "1d",
  });

  const startingMoney = quotes[0].open!;

  let money = startingMoney;
  for (let i = 0; i < days; i++) {
    // Find start and end dates
    const start = new Date();
    start.setDate(start.getDate() - days + i);

    // Skip weekends
    if (start.getDay() === 0 || start.getDay() === 6) {
      // console.log(`Skipping ${start.toDateString()}...`);
      continue;
    }

    const end = new Date();
    end.setDate(start.getDate() + 1);

    try {
      money = await testSingleDay(symbol, money, start, end, config);
    } catch (e) {
      // console.log(`Error on ${start.toDateString()}`);
    }
  }

  // console.log("-------------------");
  // console.log(`Starting Money: $${startingMoney}`);

  // Find ending share price
  const finalPrice = quotes[quotes.length - 1].open;
  // console.log(`Final Price: $${finalPrice}`);

  // console.log(`Final Money: $${money}`);
  // console.log(`Total Profit: $${money - startingMoney}`);

  // Calculate % profit
  const profitPercent = (money - startingMoney) / startingMoney;

  // console.log(`Total Profit %: ${Math.round(profitPercent * 10000) / 100}%`);

  return profitPercent;
};

const main = async () => {
  let bestConfig = new Config(),
    bestProfit: number | null = null;

  let config = new Config();
  for (let i = 0; i < 100; i++) {
    console.log(`Testing config ${i}...`);
    console.log(config);

    const profit = await testMultiDay("AAPL", 15, config);

    if (!bestProfit || profit > bestProfit) {
      bestProfit = profit;
      bestConfig = config;
    }

    console.log(`Profit: ${profit} vs. ${bestProfit}`);

    config = config.mutate();
  }

  console.log("Best config:");
  console.log(bestConfig);
  console.log("Best profit:");
  console.log(bestProfit);
};

main();
