import csv
import pandas as pd
import urllib
import datetime
import pickle
import numpy as np;

df = pd.read_csv('../Data/companylist.csv')
stock_tickers = df.Symbol

#  Save results for each stock in a folder

final_results = {};

##  Calculate moving average for all points over n data points in a list,
##  then also removes n - 1 data points and returns that as a separate list

def calculateMovingAverageList(data, n):    
    currentAverage = 0;
    internalValues = [];
    movingAverage = [];

    for i in range(n):
        # Append all values to internalValues;
        # print i;
        internalValues.append(data[i]);
        
    currentAverage = np.mean(internalValues);
    movingAverage.append(currentAverage);
        
    for i in range(n + 1, len(data)):
        # print i;
        del internalValues[0]; # Delete first index
        internalValues.append(data[i]); # Add data at i;
        currentAverage = np.mean(internalValues);
        movingAverage.append(currentAverage);
        
    return movingAverage, data[n:];

def fixTimeData(timeList, n, data, movingAverage):
    for i in range(n):
        timeList.append(i);
        movingAverage.insert(0, 0);
        
    for j in range(i, len(data) - 1):
        timeList.append(j)
        
    return movingAverage;


def calculateSlope(movingAverageList):
    dX = 1.0;
    dY = [];
    
    for i in range(len(movingAverageList) - 1):
        dY.append(movingAverageList[i + 1] - movingAverageList[i]);
        
    dY.append(movingAverageList[i + 1]);
    slope = [dy / dX for dy in dY];
    return slope;


## range = start, stop
for i in range(len(stock_tickers)):
    print "Currently calculating for stock: " + stock_tickers[i] + " (progress: " + str(i) + " of " + str(len(stock_tickers)) + ")"
    filename = "../Data_From_Script/getprices_" + stock_tickers[i] + "_long.txt"
    # urllib.urlretrieve('http://finance.google.com/finance/getprices?i=600&p=300d&f=d,o,h,l,c,v&df=cpct&q=' + stock_tickers[i], filename);

    dataDict = {};
    times = [];
    closing = [];
    skipBoolean = False;

    with open(filename, 'rb') as csvfile:
        pricereader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for i, row in enumerate(pricereader):
            if i > 6:
                dataDict[i] = row;
                try:
                    values = row[0].split(',');
                    times.append(values[0]);
                    closing.append(float(values[1]));
                except IndexError:
                    skipBoolean = True;
                    continue;


    if skipBoolean == True:
        continue;

    timesUTC = [];

    currUnixTime = 0;
    currTime = None;

    for i in range(len(times)):
        if times[i][0] == 'a':
            #print i;
            currUnixTime = int(times[i][1:]);
            #print currUnixTime;
            currTime = datetime.datetime.utcfromtimestamp(currUnixTime)
            #print currTime
            timesUTC.append(currTime);
        else:
            #print currUnixTime
            timesUTC.append(datetime.datetime.utcfromtimestamp(currUnixTime + int(times[i])));

    #movingAverage50, shorterData50 = calculateMovingAverageList(closing, 50);
    #timeStamp50 = timesUTC[50:];

    #movingAverage20, shorterData20 = calculateMovingAverageList(closing, 20);
    #timeStamp20 = timesUTC[20:];

    #movingAverage10, shorterData10 = calculateMovingAverageList(closing, 10);
    #timeStamp10 = timesUTC[10:];

    if len(closing) == 0:
        continue;

    try:
        movingAverage78, shorterData78 = calculateMovingAverageList(closing, 78);
        timeStamp78 = timesUTC[78:];
    except IndexError:
        continue;

    movingAverage5, shorterData5 = calculateMovingAverageList(closing, 5);
    timeStamp5 = timesUTC[5:];

    movingAverage39, shorterData39 = calculateMovingAverageList(closing, 39);
    timeStamp39 = timesUTC[39:];

    movingAverage20, shorterData20 = calculateMovingAverageList(closing, 20);
    timeStamp20 = timesUTC[20:];

    #import matplotlib;
    #import matplotlib.pyplot as plt
    #get_ipython().magic(u'matplotlib')

    #print timeStamp10[0];
    #print timeStamp10[1];
    #print timeStamp10[50];

    #print movingAverage10[0];
    #print movingAverage10[1];
    #print movingAverage10[50];

    fixTime5 = [];
    fixTime20 = [];
    fixTime39 = [];
    fixTime78 = [];

    movingAverage5 = fixTimeData(fixTime5, 5, closing, movingAverage5);
    movingAverage20 = fixTimeData(fixTime20, 20, closing, movingAverage20);
    movingAverage39 = fixTimeData(fixTime39, 39, closing, movingAverage39);
    movingAverage78 = fixTimeData(fixTime78, 78, closing, movingAverage78);

    # Calculate decision points

    slope78 = calculateSlope(movingAverage78);
    slope39 = calculateSlope(movingAverage39);
    slope20 = calculateSlope(movingAverage20);
    slope5 = calculateSlope(movingAverage5);

    buyPoints = [];

    if len(slope78) < len(slope5):
        continue;

    for i in range(len(slope78)):
        try:
            if (slope78[i] >= 0) and (slope39[i] > 0) and (slope20[i] > 0) and (slope5[i] > 0) and (closing[i] > movingAverage78[i]):
                buyPoints.append(i);
        except IndexError:
            continue;


    # print buyPoints;

    sellPoints = [];

    for i in range(len(slope78)):
        if (slope78[i] < 0) and (slope39[i] < 0) and (slope20[i] < 0) and (slope5[i] < 0) and (closing[i] < movingAverage78[i]):
            sellPoints.append(i);

    ##  Find one buyPoint and one sellPoint

    buy_sell_Points_tuple_list = []

    for buyPoint in buyPoints:
        buy_sell_Points_tuple_list.append((buyPoint, "buy"));

    for sellPoint in sellPoints:
        buy_sell_Points_tuple_list.append((sellPoint, "sell"));


    buy_sell_Points_tuple_list.sort(key=lambda tup: tup[0])  # sorts in place

    # print buy_sell_Points_tuple_list

    buy_list = [];
    sell_list = [];

    isBuy = True;

    for value in buy_sell_Points_tuple_list:
        if isBuy == True and value[1] == 'buy':
            buy_list.append(value[0]);
            isBuy = False;
        elif isBuy == False and value[1] == 'sell':
            sell_list.append(value[0]);
            isBuy = True;


    ##  Calculate earnings (from just sell minus buy)
    earnings = [];
    number_of_transactions = 0;

    for i in range(len(sell_list)):
        earnings.append(closing[sell_list[i]] - closing[buy_list[i]]);
        number_of_transactions += 1;

    for i in range(1, len(buy_list)):
        # print buy_list[i], sell_list[i - 1];
        # print closing[buy_list[i]], closing
        earnings.append(-(closing[buy_list[i]] - closing[sell_list[i - 1]]));
        number_of_transactions += 1;

    #print earnings
    #print np.sum(earnings)
    #print np.mean(earnings)
    #print np.std(earnings)


    # In[36]:

    ## Price of transaction:
    price_of_transactions = - 7 * number_of_transactions * 2;
    #print price_of_transactions;


    # In[37]:

    ## Net sum with number_of_shares amount of stock
    if len(buy_list) == 0:
        number_of_shares = 0;
    else:
        number_of_shares = 10000 / closing[buy_list[0]];
    #print np.sum(earnings) * number_of_shares - price_of_transactions;


    # In[38]:

    ## Percentage gain
    if len(buy_list) == 0:
        starting_amount = 0;
    else:
        starting_amount = closing[buy_list[0]] * number_of_shares + 7;

    final_amount = starting_amount + np.sum(earnings) * number_of_shares - price_of_transactions;

    #print final_amount / starting_amount;


    # In[40]:

    #plt.plot(closing);
    #plt.plot(fixTime5, movingAverage5);
    #plt.plot(fixTime20, movingAverage20);
    #plt.plot(fixTime39, movingAverage39);
    #plt.plot(fixTime78, movingAverage78);

    #for buy in buy_list:
    #    plt.axvline(x=buy, color='g');
        
    #for sell in sell_list:
    #    plt.axvline(x=sell, color='r');

    #plt.xlim([150, 1200]);
    #plt.ylim([235, 250]);


    # #  Data from:
    # http://finance.google.com/finance/getprices?i=600&p=30d&f=d,o,h,l,c,v&df=cpct&q=AMD

    final_results[stock_tickers[i]] = (buy_list, sell_list, number_of_shares, earnings, starting_amount, final_amount);

pickle.dump( final_results, open( "final_results_market.p", "wb" ) )




