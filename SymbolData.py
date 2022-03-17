from AlgorithmImports import *
class SymbolData(object):

    def __init__(self, symbol, barPeriod, windowSize):
        self.Symbol = symbol
        self.BarPeriod = barPeriod
        self.Bars = RollingWindow[IBaseDataBar](windowSize)
        self.RsiWindow = RollingWindow[float](windowSize)
        self.SmaWindow = RollingWindow[float](windowSize)
        self.RSI = None
        self.SMA = None
        self.invest = True
        self.sell_entry_price = 0.0
        self.entry_ticket = None
        self.leave_alone_cnt = 0
        self.param_variables = None

  
    def IsReady(self):
        return self.Bars.IsReady and self.RSI.IsReady and self.SMA.IsReady and self.RsiWindow.IsReady and self.SmaWindow.IsReady

    def WasJustUpdated(self, current):
        isInFivePeriod = current.minute % 5 == 0 
        return self.Bars.Count > 0 and isInFivePeriod