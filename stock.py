#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Jen Liu
#
# Created:     28/04/2015
# Copyright:   (c) Jen Liu 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import csv
import datetime
import urllib2
import math
import matplotlib.pyplot as plt
import numpy as np
from collections import namedtuple


today = datetime.datetime.now().strftime('%Y-%m-%d')
todayDateTime = datetime.datetime.now()
def increaseValidDate(date, prices):
    """ Increase date to a valid trading date
    """
    #do-while loop to increase date to an valid date
    while True:
        date = date + datetime.timedelta(days=1)
        if(date > todayDateTime or prices.has_key(date.strftime('%Y-%m-%d'))):
            return date

def sma(days, startDate, prices):
    """Simple moving average
    :param days: number of days to average
    :param startDate: date where average ends
    """
    stop = 0
    ma = 0
    i = days*-1
    while(i < stop and (startDate + datetime.timedelta(days=i)).strftime('%Y-%m-%d') != today):
        try:
            i = i+1
            ma = ma + float(prices[(startDate + datetime.timedelta(days=i)).strftime('%Y-%m-%d')])
        except Exception:
            stop = stop+1
    return (ma/days)

def ema(days, close, prevEMA):
    multiplier = (2.0/(days+1))
    return (close - prevEMA)*(multiplier) + prevEMA

def downloadData(symbol):
    """ Download data from yahoo finance and save the csv file to C:/stock
    """
    # Retrieve the webpage as a string
    response = urllib2.urlopen("http://ichart.finance.yahoo.com/table.csv?s="+symbol+"&c=1962")
    csv = response.read()

    # Save the string to a file
    csvstr = str(csv).strip("b'")

    lines = csvstr.split("\\n")
    filePath = "C:\\stock\\"+symbol+".csv"
    f = open(filePath, "w")
    for line in lines:
       f.write(line + "\n")
    f.close()
    return filePath

def fileToDict(symbol, date):
    """Convert csv file to dictionary
    :param symbol: stock symbol
    :param date: date to stop
    :returns last valid date to use and dictionary of date/prices
    """
    filePath = downloadData(symbol)
    f = open(filePath,"rU")
    csvreader = csv.reader(f)
    prices = {}
    #build dict until specified date
    lastDate = ""
    for row in csvreader:
        if(row[0] != date):
            prices[row[0]] = row[6]
            lastDate = row[0]
        else:
            break
    f.close()
    return lastDate, prices

def onSegment(p1, p2, p3):
    if(p2[0] <= max(p1[0], p3[0]) and p2[0] >= min(p1[0], p3[0]) and p2[1] <= max(p1[1], p3[1]) and p2[1] >= min(p1[1], p3[1])):
        return True
    return False

def orientation(p1, p2, p3):
    val = (p2[1] - p1[1]) * (p3[0] - p2[0]) - (p2[0] - p1[0]) * (p3[1] - p2[1])
    if(val == 0):
        return 0
    elif(val > 0):
        return 1
    else:
        return 2

def doIntersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    if(o1 != o2 and o3 != o4):
        return True
    if(o1 == 0 and onSegment(p1, p2, q1)):
        return True
    if(o2 == 0 and onSegment(p1, q2, q1)):
        return True
    if(o3 == 0 and onSegment(p2, p1, q2)):
        return True
    if(o4 == 0 and onSegment(p2, q1, q2)):
        return True
    return False



def tradeMACD(symbol, date, ma1, ma2, maType, fund):
 #print("Using " + str(ma1) + "-"+str(ma2))
    priceTuple = fileToDict(symbol, date)
    #verify date parameter is valid
    if(priceTuple[0] != date):
        date = priceTuple[0]
        print("Specified Date is invalid, using nearest date: "+ priceTuple[0])
    prices = priceTuple[1]
    d = datetime.datetime.strptime(date, '%Y-%m-%d')
    stock = 0
    cash = fund
    priceList = []
    maLow = None
    maHigh = None
    invested = 0
    MACD = []
    MACD_9_List = []
     #Start trading
    for j in range (0, 2000):
        now = d.strftime('%Y-%m-%d')
        nowPrice = float(prices[now])
        priceList.append(nowPrice)

        #user EMA strategy
        if(maType == "ema"):
            #finding EMA
            if(maLow == None):
                maLow = sma(ma1, d, prices)
                maHigh = sma(ma2, d, prices)
            else:
                maLow = ema(ma1, nowPrice, maLow)
                maHigh = ema(ma2, nowPrice, maHigh)
        #use SMA strategy
        else:
            maLow = sma(ma1, d, prices)
            maHigh = sma(ma2, d, prices)

        MACD.append(maLow - maHigh)

        #only start analyzing after MACD has 9 days worth of data
        if(len(MACD) > 9):
            #calculate sma of macd
            if(len(MACD_9_List) == 0):
                MACD_9 = sum(MACD[-9:])/9 #use sma first
            else:
                MACD_9 = ema(9, MACD[-1], MACD_9_List[-1])
            MACD_9_List.append(MACD_9)
            profit = 0
            #create points
            p1 = (0, MACD[-2])
            p2 = (1, MACD[-1])
            if(len(MACD_9_List) < 2):
                q1 = (0, MACD[-2])
            else:
                q1 = (0, MACD_9_List[-2])
            q2 = (1, MACD_9_List[-1])
            #Trading strategy
            #Exit point
            if (doIntersect(p1, p2, q1, q2) and p2[1]> q2[1]): # MACD above MCAD_9 and intersect
                cash = cash + stock*nowPrice
                profit = (nowPrice)*stock - invested
                invested = 0
                if(stock > 0):
                    print(now + " **Sell " +symbol+" "+str(stock)+"@"+ prices[now] + " Cash:" + str(cash) + " Profit:"+str(profit))
                    plt.axvline(x=j-9, color='g')
                stock = 0
            #Entry point
            elif (doIntersect(p1, p2, q1, q2) and p2[1] < q2[1] and p2[1] > 0): # MACD below MCAD_9 and intersect
                tmpStock = 0
                if(cash - 100*nowPrice < 0): #buy 100 stock
                    tmpStock = int(cash/nowPrice)
                    stock = stock+ tmpStock
                    cash = cash - tmpStock*nowPrice
                else: #don't have enough fund, buy less stock
                    cash = cash - 100*nowPrice
                    stock = 100
                    tmpStock = 100
                invested = invested + nowPrice*tmpStock
                plt.axvline(x=j-9, color='r')
                print(now + " Buy " + symbol + " "+str(tmpStock)+"@" + prices[now] + " Cash:" + str(cash))

            #print(now + " Short: " + str(maLow) + " Long: "+ str(maHigh) +" To Watch: "+str(maMid))

        d =increaseValidDate(d, prices)

        if(d > todayDateTime):
            break
            #Reverse last bought stock
    print("Profit for "+symbol+": "+str(cash - fund))
    plt.plot(MACD[9:])
    plt.plot(MACD_9_List)
    plt.plot(priceList[9:])
    plt.axhline(y=0)
    plt.show()
    if(stock != 0):
        cash = cash+invested

    return cash

def tradeSim(symbol, date, ma1, ma2, maType, fund):
    #print("Using " + str(ma1) + "-"+str(ma2))
    priceTuple = fileToDict(symbol, date)
    #verify date parameter is valid
    if(priceTuple[0] != date):
        date = priceTuple[0]
        print("Specified Date is invalid, using nearest date: "+ priceTuple[0])
    prices = priceTuple[1]
    d = datetime.datetime.strptime(date, '%Y-%m-%d')
    stock = 0

    prev_delta = 0
    cash = fund
    momentumIndex = 10
    priceList = []
    maLow = None
    maHigh = None
    entryPrice = 0
    for j in range (0, 2000): #Trading duration

        now = d.strftime('%Y-%m-%d')
        nowPrice = float(prices[now])
        priceList.append(nowPrice)

        if(maType == "ema"): #user EMA strategy
            #finding EMA
            if(maLow == None):
                maLow = sma(ma1, d)
                maHigh = sma(ma2, d)
            else:
                maLow = ema(ma1, nowPrice, maLow)
                maHigh = ema(ma2, nowPrice, maHigh)
        else: #use SMA strategy
            maLow = sma(ma1, d)
            maHigh = sma(ma2, d)

        stopLoss = sma(200, d)
        profit = 0
        momentum = 0
        exitCoeff = 1.1 #higher coefficient exists earlier
        if(j >= momentumIndex):
            momentum = (nowPrice - priceList[j-momentumIndex]) / nowPrice
        if prev_delta == 0:
            prev_delta  = maLow - maHigh
        #Trading strategy
        #Exit point
        elif (prev_delta > 0 and maLow < maHigh*exitCoeff) or (nowPrice < stopLoss and entryPrice > stopLoss):# or (nowPrice < min(maLow, maHigh)*.9):
            cash = cash + stock*nowPrice
            profit = (nowPrice - entryPrice)*stock
            prev_delta  = maLow - maHigh
            if(stock > 0):
                print(now + " **Sell " +symbol+" "+str(stock)+"@"+ prices[now] + " Cash:" + str(cash) + " Profit:"+str(profit))
            stock = 0
        #Entry point
        elif (prev_delta < 0 and maLow > maHigh):# or (nowPrice > max(maLow, maHigh)*1.1):
            if(cash - 100*nowPrice < 0): #buy 100 stock
                stock = int(cash/nowPrice)
                cash = cash - stock*nowPrice
            else: #don't have enough fund, buy less stock
                cash = cash - 100*nowPrice
                stock = 100
            entryPrice = nowPrice
            prev_delta  = maLow - maHigh
            print(now + " Buy " + symbol + " "+str(stock)+"@" + prices[now] + " Cash:" + str(cash))

        #print(now + " Short: " + str(maLow) + " Long: "+ str(maHigh) +" To Watch: "+str(maMid))

        d =increaseValidDate(d)

        if(d > todayDateTime):
            break
            #Reverse last bought stock
    if(stock != 0):
        cash = cash+entryPrice*stock


    return cash







if __name__ == '__main__':
    symbols = ["FB"]
    cash = 0
    fund = 0
    for s in symbols:
        fund = fund + 1000
        cash = cash + tradeMACD(s,"2013-10-03", 12,26,"ema", 1000)
        print("-------------------------------------------")
    print("Total Profit:" + str(cash - fund))
