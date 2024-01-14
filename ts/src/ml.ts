import yahooFinance from "yahoo-finance2";
import { NeuralNetwork, recurrent } from "brain.js";
import {
  INeuralNetworkData,
  INeuralNetworkDatum,
  INeuralNetworkTrainOptions,
} from "brain.js/dist/neural-network";
import { INeuralNetworkOptions } from "brain.js/dist/neural-network-types";
import { ChartResultArrayQuote } from "yahoo-finance2/dist/esm/src/modules/chart";
import { IRNNOptions } from "brain.js/dist/recurrent/rnn";
import { IRecurrentTrainingOptions } from "brain.js/dist/recurrent";

interface IData
  extends INeuralNetworkDatum<
    Partial<INeuralNetworkData>,
    Partial<INeuralNetworkData>
  > {}

function getInput(quotes: ChartResultArrayQuote[]): number[] {
  const prices = quotes.map((quote) => quote.close! / quote.open! - 0.5);
  prices.push(
    quotes[quotes.length - 1].open! / quotes[quotes.length - 2].close! - 0.5
  );

  return prices;
}

async function main() {
  const end = new Date();
  const start = new Date();
  // start.setDate(end.getDate() - 150);
  start.setFullYear(end.getFullYear() - 5);

  const symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA"];

  // Input length must always be the same
  const prevDaysConsidered = 3;
  const trainingRatio = 0.9;
  const trainingData: IData[] = [];

  // Generate training set
  for (const symbol of symbols) {
    const fetchedData = await yahooFinance.chart(symbol, {
      period1: start.toDateString(),
      period2: end.toDateString(),
      interval: "1d",
    });

    for (
      let i = prevDaysConsidered;
      i < fetchedData.quotes.length * trainingRatio;
      i++
    ) {
      const quote = fetchedData.quotes[i];

      // Skip weekends
      if (quote.date.getDay() === 0 || quote.date.getDay() === 6) continue;

      // Format and normalize the data
      const quotes = fetchedData.quotes.slice(i - prevDaysConsidered, i);

      trainingData.push({
        input: getInput(quotes),
        output: [quote.close! / quote.open! - 0.5],
      });
    }
  }

  const net = new recurrent.LSTMTimeStep({
    log: true,
    logPeriod: 10,
  });

  console.log("Starting training...");
  net.train(trainingData as any);
  console.log("Training finished!");

  const fetchedData = await yahooFinance.chart("AAPL", {
    period1: start.toDateString(),
    period2: end.toDateString(),
    interval: "1d",
  });

  // Try out the network
  for (
    let i = Math.floor(fetchedData.quotes.length * trainingRatio);
    i < fetchedData.quotes.length;
    i++
  ) {
    const quote = fetchedData.quotes[i];

    // Skip weekends
    if (quote.date.getDay() === 0 || quote.date.getDay() === 6) continue;

    const quotes = fetchedData.quotes.slice(i - prevDaysConsidered, i);

    const predicted = net.run(getInput(quotes)) as any as number;

    console.log(
      `Actual: ${quote.close! / quote.open! - 1}, predicted: ${predicted - 0.5}`
    );
  }
}

main();
