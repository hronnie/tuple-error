#region imports
from AlgorithmImports import *
#endregion


class PullBackScalperAlgo(object): 

    def __init__(self, symbolData, params, Time):
        self.symbolData = symbolData
        self.params = params

    def isDataPointSatisfied(self):
        """
        Public method for Pull Back algo. Returns true if datapoint satisfies all algo conditions
        """        
        if self.__isRedCandleConditionSatisfied() == False:
            return False
        if self.__isPreviousCandleGreenConditionSatisfied() == False:
            return False
        if self.__isSmallWickedRedCandleSatisfied() == False:
            return False
        if self.__isBreakOutConfirmedSatisfied() == False: 
            return False
        if self.__isBigVolumeChangeSatisfied() == False: 
            return False
        if self.__isBigPriceChangeSatisfied() == False: 
            return False
        if self.__isRsiConditionSatisfied() == False: 
            return False

        return True

    # DEBUG PURPOSE ONLY
    def getParamValues(self): 
        order_params = {}

        green_candle_lows = np.array([])
        green_candle_highs = np.array([])
        i = -1
        for i in np.arange(0, self.symbolData.Bars.Size  - 1, 1): 
            i += 1
            if i == 0:
                continue
            if self.symbolData.Bars[i].Close > self.symbolData.Bars[i].Open:
                green_candle_lows = np.append(green_candle_lows, self.symbolData.Bars[i].Low)
                green_candle_highs = np.append(green_candle_highs, self.symbolData.Bars[i].High)
            else: 
                break

        priceChangePerc = 100 - ((green_candle_lows.min() / green_candle_highs.max()) * 100)
        

        order_params["minPriceChangePerc"] = priceChangePerc

        fullCandleHeight = self.symbolData.Bars[0].High - self.symbolData.Bars[0].Low
        lowerWickHeight = self.symbolData.Bars[0].Close - self.symbolData.Bars[0].Low
        candleWickPerc = (lowerWickHeight / fullCandleHeight) * 100         
        

        prevGreenCandleLowDistFromSma = 100 - ((self.symbolData.SmaWindow[1] / self.symbolData.Bars[1].Low) * 100)
        isLastGreenCandleFarEnough = prevGreenCandleLowDistFromSma > self.params["smaPrevGreenCandleLowPerc"]
        
        prevGreenCandleMovePerc = 100 - ((self.symbolData.SmaWindow[1] / self.symbolData.Bars[1].High) * 100)
        prevGreenCandleHasBigBody = 100 - (((self.symbolData.Bars[1].Close - self.symbolData.Bars[1].Open) / (self.symbolData.Bars[1].High - self.symbolData.Bars[1].Low)) * 100)
        isHugeGreenCandle = self.params["smaPrevGreenCandleHighPerc"] <= prevGreenCandleMovePerc and prevGreenCandleHasBigBody > 70
        
        order_params["maximumCandleWickDistPerc"] = candleWickPerc
        order_params["smaPrevGreenCandleHighPerc"] = prevGreenCandleMovePerc
        order_params["smaPrevGreenCandleLowPerc"] = prevGreenCandleLowDistFromSma

        green_candle_volumes = np.array([])
        i = -1
        for i in np.arange(0, self.symbolData.Bars.Size - 1, 1): 
            i += 1
            if i == 0:
                continue
            if self.symbolData.Bars[i].Close > self.symbolData.Bars[i].Open:
                green_candle_volumes = np.append(green_candle_volumes, self.symbolData.Bars[i].Volume)
            else: 
                break

        if (i < 9): 
            green_candle_volumes = np.append(green_candle_volumes, self.symbolData.Bars[i].Volume)

        volume_change_array = np.array([])
        for i in np.arange(len(green_candle_volumes) - 1, 0, -1):
            volume_change_array = np.append(volume_change_array, green_candle_volumes[i - 1] / green_candle_volumes[i])
        
        volumeChangePerc = volume_change_array.max() * 100

        order_params["minVolumeChangePerc"] = volumeChangePerc
        return order_params
    # DEBUG PURPOSE ONLY
        

    def __isRedCandleConditionSatisfied(self): 
        """
        Is the current candle a red candle?
        """
        return self.symbolData.Bars[0].Open > self.symbolData.Bars[0].Close
            
    def __isPreviousCandleGreenConditionSatisfied(self):
        """
        Is the previous candle a green candle?
        """
        return self.symbolData.Bars[1].Open < self.symbolData.Bars[1].Close

    def __isSmallWickedRedCandleSatisfied(self): 
        """
        Does the last red candle have a small wick? - maximumCandleWickDistPerc
        """
        fullCandleHeight = self.symbolData.Bars[0].High - self.symbolData.Bars[0].Low
        lowerWickHeight = self.symbolData.Bars[0].Close - self.symbolData.Bars[0].Low
        candleWickPerc = (lowerWickHeight / fullCandleHeight) * 100         
        return candleWickPerc < self.params["maximumCandleWickDistPerc"]
                
    def __isBreakOutConfirmedSatisfied(self): 
        """
        Considering the previous green candle was it a significant pump?
            - It was if there was a hug green candle - smaPrevGreenCandleHighPerc
            - Or the last green candle is far enough from the SMA (5) line - smaPrevGreenCandleLowPerc
        """
        prevGreenCandleLowDistFromSma = 100 - ((self.symbolData.SmaWindow[1] / self.symbolData.Bars[1].Low) * 100)
        isLastGreenCandleFarEnough = prevGreenCandleLowDistFromSma > self.params["smaPrevGreenCandleLowPerc"]
        
        prevGreenCandleMovePerc = 100 - ((self.symbolData.SmaWindow[1] / self.symbolData.Bars[1].High) * 100)
        prevGreenCandleHasBigBody = 100 - (((self.symbolData.Bars[1].Close - self.symbolData.Bars[1].Open) / (self.symbolData.Bars[1].High - self.symbolData.Bars[1].Low)) * 100)
        isHugeGreenCandle = self.params["smaPrevGreenCandleHighPerc"] <= prevGreenCandleMovePerc and prevGreenCandleHasBigBody > 70
        
        return isLastGreenCandleFarEnough == True or isHugeGreenCandle == True

    def __isBigVolumeChangeSatisfied(self):
        """
        Was there a big volume change for green candles? - minVolChangePerc
        """        
        green_candle_volumes = np.array([])
        i = -1
        for i in np.arange(0, self.symbolData.Bars.Size - 1, 1): 
            i += 1
            if i == 0:
                continue
            if self.symbolData.Bars[i].Close > self.symbolData.Bars[i].Open:
                green_candle_volumes = np.append(green_candle_volumes, self.symbolData.Bars[i].Volume)
            else: 
                break

        if (i < 9): 
            green_candle_volumes = np.append(green_candle_volumes, self.symbolData.Bars[i].Volume)

        volume_change_array = np.array([])
        for i in np.arange(len(green_candle_volumes) - 1, 0, -1):
            volume_change_array = np.append(volume_change_array, green_candle_volumes[i - 1] / green_candle_volumes[i])
        
        volumeChangePerc = volume_change_array.max() * 100

        return volumeChangePerc > self.params["minVolChangePerc"]


    def __isBigPriceChangeSatisfied(self):
        """
        Was there a big price change for green candles? - minPriceChangePerc
        """
        green_candle_lows = np.array([])
        green_candle_highs = np.array([])
        i = -1
        for i in np.arange(0, self.symbolData.Bars.Size  - 1, 1): 
            i += 1
            if i == 0:
                continue
            if self.symbolData.Bars[i].Close > self.symbolData.Bars[i].Open:
                green_candle_lows = np.append(green_candle_lows, self.symbolData.Bars[i].Low)
                green_candle_highs = np.append(green_candle_highs, self.symbolData.Bars[i].High)
            else: 
                break

        priceChangePerc = 100 - ((green_candle_lows.min() / green_candle_highs.max()) * 100)
        return priceChangePerc > self.params["minPriceChangePerc"]
        

    def __isRsiConditionSatisfied(self): 
        """
        Did RSI went above 90 and then came back below 90?
        """
        green_candle_rsis = np.array([])
        i = -1
        for i in np.arange(0, self.symbolData.Bars.Size  - 1, 1): 
            i += 1
            if i == 0:
                continue
            if self.symbolData.Bars[i].Close > self.symbolData.Bars[i].Open:
                green_candle_rsis = np.append(green_candle_rsis, self.symbolData.RsiWindow[i])
            else: 
                break

        # RSI went above 90 and then came back to below at least 90?
        green_candle_rsis = green_candle_rsis[green_candle_rsis >= 90]
        isRsiUpTo90 = len(green_candle_rsis) > 0
        return isRsiUpTo90 == True and self.symbolData.RsiWindow[0] < 90

             
