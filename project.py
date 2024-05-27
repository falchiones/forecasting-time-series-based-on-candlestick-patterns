import pandas as pd

# переворачиваем данные для правильной их обработки
def reverseData(inputPath, outputPath):
    data = pd.read_csv(inputPath, delimiter=',')
    reversedData = data.iloc[::-1]
    reversedData.to_csv(outputPath, index=False, sep=',')
    print(f'Data reversed and saved in {outputPath}')

# задаем шаблоны кодирования свечей и применяем их к каждому ряду данных
def encodeCandlestickPatterns(inputPath, outputPath):
    data = pd.read_csv(inputPath, delimiter=',')
    print("Columns in the loaded data:", data.columns)
    data = data[['date', 'op', 'hp', 'lp', 'cp']]
    
    def candlestickEncoder(row):
        openPrice, highPrice, lowPrice, closePrice = row['op'], row['hp'], row['lp'], row['cp']
        if highPrice > openPrice > closePrice > lowPrice:
            return 'a'
        elif highPrice == openPrice > closePrice > lowPrice:
            return 'b'
        elif highPrice > openPrice == closePrice > lowPrice:
            return 'c'
        elif highPrice > openPrice > closePrice == lowPrice:
            return 'd'
        elif highPrice > closePrice > openPrice > lowPrice:
            return 'e'
        elif highPrice == closePrice > openPrice > lowPrice:
            return 'f'
        elif highPrice > closePrice == openPrice > lowPrice:
            return 'g'
        elif highPrice > closePrice > lowPrice == openPrice:
            return 'h'
        elif highPrice == openPrice == closePrice > lowPrice:
            return 'i'
        elif highPrice > openPrice == closePrice == lowPrice:
            return 'j'
        elif highPrice == closePrice > openPrice == lowPrice:
            return 'k'
        elif highPrice > openPrice == lowPrice == closePrice:
            return 'l'
        else:
            print(f"Row doesn't match any rule: {row}")
            return None

    data['code'] = data.apply(candlestickEncoder, axis=1)
    data.to_csv(outputPath, index=False, sep=',', encoding='utf-8')
    print(f'Encoded data saved in {outputPath}')

# идентифицируем точки изменения в данных, сегментируем последние на основе этих точек, а также определяем тренды
def segmentAndLabelTrends(inputPath, outputPath):
    data = pd.read_csv(inputPath, delimiter=',')
    data['date'] = pd.to_datetime(data['date'], format='%d.%m.%Y')
    closePrices = data['cp'].tolist()
    codes = data['code'].tolist()

    def findChangePoints(prices, codes):
        changePoints = [(0, 'Start', codes[0])]
        for i in range(1, len(prices) - 1):
            leftPrice, currentPrice, rightPrice = prices[i - 1], prices[i], prices[i + 1]
            if leftPrice != currentPrice or currentPrice != rightPrice or codes[i] != codes[i-1] or codes[i] != codes[i+1]:
                changePoints.append((i, codes[i], 'Change'))
        changePoints.append((len(prices) - 1, 'End', codes[-1]))
        return changePoints

    changePoints = findChangePoints(closePrices, codes)[:-1]

    def segmentTrends(prices, changePoints):
        segments = []
        trends = []
        for i in range(1, len(changePoints)):
            start, end = changePoints[i - 1][0], changePoints[i][0]
            segment = prices[start:end + 1]
            segments.append(segment)
            trend = 'Up' if segment[0] < segment[-1] else 'Down' if segment[0] > segment[-1] else 'Equal'
            trends.append(trend)
        return segments, trends

    segments, trends = segmentTrends(closePrices, changePoints)

    def createPatterns(changePoints, trends):
        return [{'segment': f'{changePoints[i][1]}-{changePoints[i + 1][1]}', 'trend': trends[i]} for i in range(len(trends))]

    patterns = createPatterns(changePoints, trends)
    patternsDf = pd.DataFrame(patterns)
    patternsDf.to_csv(outputPath, index=False, sep=',')
    print(f'Patterns saved in {outputPath}')

# создаём набор паттернов, прогнозируем следующий тренд на основе текущего паттерна
def generatePatternRecordSet(inputPath, outputPath):
    patternSet = pd.read_csv(inputPath, delimiter=',')

    def isSubsequence(X, Y):
        lenX, lenY = len(X), len(Y)
        if lenX > lenY:
            return 0
        i, k = 0, 0
        while i < lenX:
            if k == lenY:
                return 0
            for j in range(k, lenY):
                if X[i] == Y[j]:
                    i += 1
                    k = j + 1
                    break
                elif j == lenY - 1:
                    return 0
        return 1

    def createRecordSet(patternSet):
        recordSet = []
        for i in range(len(patternSet)):
            sameTrendCount = 0
            occurrenceCount = 0
            segmentI = patternSet.iloc[i]['segment']
            trendI = patternSet.iloc[i]['trend']
            for j in range(len(patternSet)):
                segmentJ = patternSet.iloc[j]['segment']
                trendJ = patternSet.iloc[j]['trend']
                isSub = isSubsequence(segmentI, segmentJ)
                if isSub:
                    occurrenceCount += 1
                    if trendI == trendJ:
                        sameTrendCount += 1
            pacc = (sameTrendCount / occurrenceCount) * 100 if occurrenceCount != 0 else 0
            recordSet.append({'segment': segmentI, 'trend': trendI, 'occurrenceCount': occurrenceCount, 'sameTrendCount': sameTrendCount, 'PACC': pacc})
        return recordSet

    patternRecordSet = createRecordSet(patternSet)
    patternRecordSetDf = pd.DataFrame(patternRecordSet)
    patternRecordSetDf.to_csv(outputPath, index=False, sep=',')
    print(patternRecordSetDf)

    def forecastTrend(currentPattern, recordSet):
        matches = [(row['segment'], row['trend'], row['PACC']) for _, row in recordSet.iterrows() if isSubsequence(currentPattern, row['segment'])]
        if not matches:
            return "No matching patterns to forecast"
        bestMatch = sorted(matches, key=lambda x: x[2], reverse=True)[0]
        return bestMatch[1]

    currentSegment = patternSet['segment'].iloc[-1]
    print(f'Last segment to forecast: {currentSegment}')
    predictedTrend = forecastTrend(currentSegment, patternRecordSetDf)
    print(f'Forecasting trend for last segment ({currentSegment}): {predictedTrend}')

inputFilePath = 'rusal.csv'
reversedDataFilePath = 'reversedData.csv'
encodedDataFilePath = 'encodedData.csv'
patternsFilePath = 'patternSet.csv'
patternRecordFilePath = 'patternRecordSet.csv'

reverseData(inputFilePath, reversedDataFilePath)
encodeCandlestickPatterns(reversedDataFilePath, encodedDataFilePath)
segmentAndLabelTrends(encodedDataFilePath, patternsFilePath)
generatePatternRecordSet(patternsFilePath, patternRecordFilePath)
