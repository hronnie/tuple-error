from AlgorithmImports import *
from SymbolData import *
from PullBackScalperAlgo import *
import numpy as np

class PullbackScannerAlgo(QCAlgorithm):

    # --------------------
    def Initialize(self):
        self.InitAlgoParams()
        self.InitAssets()
        self.InitData()
        self.InitBacktestParams()        
        
    # --------------------
    def InitBacktestParams(self):
        self.SetStartDate(2022, 3, 1)
        self.SetEndDate(2022, 3, 2)  
        self.SetCash(100000)

    # --------------------
    def InitData(self):
        self.UniverseSettings.Resolution = Resolution.Minute
        BarPeriod = TimeSpan.FromMinutes(5)
        RsiPeriod = 2
        SimpleMovingAveragePeriod = 5
        RollingWindowSize = 10
        self.loss = 0
        self.win = 0
        self.leave = 0
        self.Data = {}
        self.win_param_array = np.array([])
        self.loss_param_array = np.array([])
        self.leave_param_array = np.array([])

        self.UniverseSymbols = ["SOLUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "BTCUSDT", "LUNAUSDT", "FTMUSDT", "GALAUSDT", "ATOMUSDT", "NEARUSDT", "AVAXUSDT", "XRPUSDT", "SANDUSDT", "KNCUSDT", "MATICUSDT", "DOTUSDT", "MANAUSDT", "RUNEUSDT", "LINKUSDT", "LTCUSDT", "PEOPLEUSDT", "DOGEUSDT", "ETCUSDT", "DYDXUSDT", "AXSUSDT", "ONEUSDT", "THETAUSDT", "RENUSDT", "FILUSDT", "ICPUSDT", "VETUSDT", "CRVUSDT", "ALICEUSDT", "ALGOUSDT", "XTZUSDT", "ZECUSDT", "ROSEUSDT", "TOMOUSDT", "EOSUSDT", "AAVEUSDT", "SUSHIUSDT", "UNFIUSDT", "BCHUSDT", "UNIUSDT", "API3USDT", "NEOUSDT", "TRXUSDT", "LRCUSDT", "CELRUSDT", "CHZUSDT", "ARUSDT", "TLMUSDT", "YFIUSDT", "ENJUSDT", "XLMUSDT", "SXPUSDT", "OMGUSDT", "CHRUSDT", "HNTUSDT", "ZRXUSDT", "1INCHUSDT", "DUSKUSDT", "GRTUSDT", "DENTUSDT", "DODOUSDT", "DASHUSDT", "ONTUSDT", "SKLUSDT", "HBARUSDT", "XMRUSDT", "LINAUSDT", "AKROUSDT", "COMPUSDT", "QTUMUSDT", "ANTUSDT", "KAVAUSDT", "BANDUSDT", "HOTUSDT", "OCEANUSDT", "ZENUSDT", "REEFUSDT", "ICXUSDT", "BELUSDT", "SNXUSDT", "IOTAUSDT"]
        # self.UniverseSymbols = ["SOLUSDT"]

        for symbol in self.UniverseSymbols:
            crypto = self.AddCrypto(symbol)
            self.Data[symbol] = SymbolData(crypto.Symbol, BarPeriod, RollingWindowSize)
            
        for symbol, symbolData in self.Data.items():
            symbolData.SMA = SimpleMovingAverage(self.CreateIndicatorName(symbol, "SMA" + str(SimpleMovingAveragePeriod), Resolution.Minute), SimpleMovingAveragePeriod)
            symbolData.RSI = RelativeStrengthIndex(10, MovingAverageType.Simple)
            consolidator = TradeBarConsolidator(BarPeriod)
            consolidator.DataConsolidated += self.OnDataConsolidated
            self.SubscriptionManager.AddConsolidator(symbolData.Symbol, consolidator)

    # --------------------
    def InitAlgoParams(self):
        self.minPriceChangePerc = float(self.GetParameter('minPriceChangePerc')) # how big is the price change in percent
        self.minVolChangePerc = int(self.GetParameter('minVolumeChangePerc')) # how big the volume change in percent
        self.sellEntryDistance = float(self.GetParameter('sellEntryDistance'))  # the entry will be below the last red candle. this parameter is for that distance
        self.takeProfitPerc = int(self.GetParameter('takeProfitPerc'))  # Take profit percent
        self.leaveAloneTimeDiff = int(self.GetParameter('leaveAloneTimeDiff')) # if there is a possible entry then it won't be triggered immediately. how much candle do we wait to happen?
        self.maximumCandleWickDistPerc = int(self.GetParameter('maximumCandleWickDistPerc')) # how big is the wick for the last red candle?
        self.smaPrevGreenCandleLowPerc = float(self.GetParameter('smaPrevGreenCandleLowPerc')) # distance percent of sma and previous green candles low
        self.smaPrevGreenCandleHighPerc = float(self.GetParameter('smaPrevGreenCandleHighPerc')) # distance percent of sma and previous green candles high
        
        self.params = {}
        self.params["minPriceChangePerc"] = float(self.GetParameter('minPriceChangePerc')) # how big is the price change in percent
        self.params["minVolChangePerc"] = int(self.GetParameter('minVolumeChangePerc')) # how big the volume change in percent
        self.params["sellEntryDistance"] = float(self.GetParameter('sellEntryDistance'))  # the entry will be below the last red candle. this parameter is for that distance
        self.params["takeProfitPerc"] = int(self.GetParameter('takeProfitPerc'))  # Take profit percent
        self.params["leaveAloneTimeDiff"] = int(self.GetParameter('leaveAloneTimeDiff')) # if there is a possible entry then it won't be triggered immediately. how much candle do we wait to happen?
        self.params["maximumCandleWickDistPerc"] = int(self.GetParameter('maximumCandleWickDistPerc')) # how big is the wick for the last red candle?
        self.params["smaPrevGreenCandleLowPerc"] = float(self.GetParameter('smaPrevGreenCandleLowPerc')) # distance percent of sma and previous green candles low
        self.params["smaPrevGreenCandleHighPerc"] = float(self.GetParameter('smaPrevGreenCandleHighPerc')) # distance percent of sma and previous green candles high
        
    
    # --------------------
    def InitAssets(self):    
        self.SetBrokerageModel(BrokerageName.Binance, AccountType.Margin)
        self.SetAccountCurrency("USDT")
        self.EnableAutomaticIndicatorWarmUp = True
    
    # --------------------    
    def OnDataConsolidated(self, sender, bar):
        self.Data[bar.Symbol.Value].SMA.Update(bar.Time, bar.Close)
        self.Data[bar.Symbol.Value].RSI.Update(bar.Time, bar.Close)
        self.Data[bar.Symbol.Value].RsiWindow.Add(self.Data[bar.Symbol.Value].RSI.Current.Value)
        self.Data[bar.Symbol.Value].SmaWindow.Add(self.Data[bar.Symbol.Value].SMA.Current.Value)
        self.Data[bar.Symbol.Value].Bars.Add(bar)


    # --------------------
    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status != OrderStatus.Filled:
            return
        
        symbol = orderEvent.Symbol.Value
        symbolData = self.Data[orderEvent.Symbol.Value]

        if symbolData.entry_ticket is not None and symbolData.entry_ticket.OrderId == orderEvent.OrderId:
            self.Debug('a')

    # --------------------    
    def OnData(self, dataSlice):                
        # loop through each symbol in our structure
        # DEBUG PURPOSE ONLY
        if self.Time.year == 2022 and self.Time.month == 3 and self.Time.day == 2 and self.Time.hour == 23 and self.Time.minute == 0:
            self.Log('Win array. Length: ' + str(len(self.win_param_array)))
            self.Log(self.win_param_array)
            self.Log('Loss array. Length: ' + str(len(self.loss_param_array)))
            self.Log(self.loss_param_array)
        # DEBUG PURPOSE ONLY

        for symbol in self.Data.keys():
            
            symbolData = self.Data[symbol]

            # DEBUG PURPOSE ONLY
            if self.Time.year == 2022 and self.Time.month == 3 and self.Time.day == 2 and self.Time.hour == 3 and self.Time.minute == 50 and symbol == "RENUSDT":
                profit = self.Portfolio[symbol].UnrealizedProfitPercent
                profit = self.Portfolio[symbol].UnrealizedProfitPercent
            # DEBUG PURPOSE ONLY

            if (symbolData.IsReady() and symbolData.WasJustUpdated(self.Time) and symbolData.invest == False):
                # take profit / stop loss
                profit = self.Portfolio[symbol].UnrealizedProfitPercent
                if (profit >= self.takeProfitPerc * 0.01 or profit <= -0.02): 
                    symbolData.invest = True
                    self.Liquidate(symbol)                  
                if (profit >= self.takeProfitPerc * 0.01):
                    self.win_param_array = np.append(self.win_param_array, symbolData.param_variables)

                if (profit <= -0.02):
                    self.loss_param_array = np.append(self.loss_param_array, symbolData.param_variables)     

                # leave alone time is over
                symbolData.leave_alone_cnt += 1
                if symbolData.leave_alone_cnt >= self.leaveAloneTimeDiff:
                    self.Liquidate(symbol)
                    symbolData.invest = True
                    self.leave_param_array = np.append(self.leave_param_array, symbolData.param_variables)          
            

            if (symbolData.IsReady() and symbolData.WasJustUpdated(self.Time) and symbolData.invest == True):
                pullback_algo = PullBackScalperAlgo(symbolData, self.params, self.Time)
                isDatapointOk = pullback_algo.isDataPointSatisfied()
                if isDatapointOk == False:
                    continue

                symbolData.sell_entry_price = symbolData.Bars[0].Low - (symbolData.Bars[0].Low * (self.sellEntryDistance / 100))
                symbolData.invest = False
                quantity = 1000 / symbolData.Bars[0].Low
                symbolData.param_variables = pullback_algo.getParamValues()
                symbolData.entry_ticket = self.StopLimitOrder(symbol, -quantity, symbolData.sell_entry_price, symbolData.sell_entry_price)
                
                