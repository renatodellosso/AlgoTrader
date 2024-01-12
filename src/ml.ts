import yahooFinance from "yahoo-finance2";
import { NeuralNetwork, NeuralNetworkGPU, recurrent } from "brain.js";
import {
  INeuralNetworkData,
  INeuralNetworkDatum,
  INeuralNetworkTrainOptions,
} from "brain.js/dist/neural-network";
import { INeuralNetworkOptions } from "brain.js/dist/neural-network-types";
import { INumberHash } from "brain.js/dist/lookup";

interface IData
  extends INeuralNetworkDatum<
    Partial<INeuralNetworkData>,
    Partial<INeuralNetworkData>
  > {}

async function main() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 5);

  const fetchedData = await yahooFinance.chart("AAPL", {
    period1: start.toDateString(),
    period2: end.toDateString(),
    interval: "1d",
  });

  // Input length must always be the same
  const prevDaysConsidered = 10;
  const trainingRatio = 0.9;

  // Generate training set
  const trainingData: IData[] = [];
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
    const prices = quotes.map((quote) => quote.close! / quote.open! - 0.5);
    prices.push(quote.open! / quotes[quotes.length - 1].close! - 0.5);

    const volumes = quotes.map((quote) => quote.volume!);

    const input: INumberHash = {};
    for (let i = 0; i < prices.length; i++) {
      const price = prices[i];
      input[i.toString()] = price;
    }
    for (let i = 0; i < volumes.length; i++) {
      const volume = volumes[i];
      input[`${i.toString()}-volume`] = volume;
    }

    trainingData.push({
      input: prices,
      output: { change: quote.close! / quote.open! - 0.5 },
    });
  }

  const netConfig: Partial<INeuralNetworkOptions & INeuralNetworkTrainOptions> =
    {
      iterations: 20000,
      learningRate: 0.6,
      errorThresh: 0.0002,
      hiddenLayers: [7],
      activation: "leaky-relu",
      log: true,
      logPeriod: 2500,
    };

  const net = new NeuralNetwork(netConfig);

  console.log("Starting training...");
  net.train(trainingData as any, netConfig);
  console.log("Training finished!");

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
    const prices = quotes.map((quote) => quote.close!);
    prices.push(quote.open!);

    const volumes = quotes.map((quote) => quote.volume!);

    const input: INumberHash = {};
    for (let i = 0; i < prices.length; i++) {
      const price = prices[i];
      input[i.toString()] = price;
    }
    for (let i = 0; i < volumes.length; i++) {
      const volume = volumes[i];
      input[`${i.toString()}-volume`] = volume;
    }

    const predicted = net.run(prices) as any;

    console.log(
      `Actual: ${quote.close! / quote.open! - 0.5}, predicted: ${
        predicted.change
      }`
    );
  }
}

main();
