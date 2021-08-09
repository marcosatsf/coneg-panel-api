from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import numpy as np
import os
import pickle
import pandas as pd
import yaml

class TimeSeriesLSTM:
    def __init__(self, f_model_creation=False) -> None:
        self.url_repo = 'https://raw.githubusercontent.com/seade-R/dados-covid-sp/master/data/dados_covid_sp.csv'
        self.crashed = False
        if self.crashed:
            print("Unavailable model!")
        elif f_model_creation:
            self.response = self.create_model()
        else:
            try:
                with open(f'.{os.sep}shr-data{os.sep}cache_cases.pckl', 'rb') as f:
                    self.response = pickle.load(f)
            except Exception as e:
                self.response = self.create_model()


    def create_model(self):
        try:
            df_loaded = pd.read_csv(self.url_repo, delimiter=';', usecols=['nome_munic','casos_novos','datahora'])
            with open(f'.{os.sep}shr-data{os.sep}config_location.yaml', 'r') as f:
                data = yaml.load(f)
                # data['city'] to access current city
            df_filtered = df_loaded[df_loaded.nome_munic==data['city']]
            locale = f"{data['city']} - {data['state']}"
        except Exception as e:
            self.crashed = True
            raise e

        def create_dataset(dataset, look_back=1):
            dataX, dataY = [], []
            for i in range(len(dataset)-look_back-1):
                dataX.append(dataset[i:(i+look_back), 0])
                dataY.append(dataset[i + look_back, 0])
            return np.array(dataX), np.array(dataY)

        df_cases = df_filtered[:]['casos_novos'].values.astype('float32')
        df_cases = df_cases.reshape(len(df_cases),1)

        np.random.seed(7)

        scaler = MinMaxScaler(feature_range=(0, 1))
        df_cases = scaler.fit_transform(df_cases)

        look_back = 4
        trainX, trainY = create_dataset(df_cases, look_back)

        trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

        model = Sequential()
        model.add(LSTM(4, input_shape=(1, look_back)))
        model.add(Dense(4))
        model.add(Dense(1))
        model.compile(loss='mean_squared_error', optimizer='adam')
        model.fit(trainX, trainY, epochs=40, batch_size=1, verbose=1)

        predict = model.predict(np.reshape(df_cases[-4:], (1,1,4)))
        predict = scaler.inverse_transform(predict)

        last_cases = np.reshape(scaler.inverse_transform(df_cases[-6:]), (6,))
        week_cases = np.append(last_cases,round(predict[0][0]))
        week_cases = {day:int(cases) for day, cases in zip(df_filtered[-len(week_cases):]['datahora'], week_cases)}

        #model.save(f'.{os.sep}shr-data{os.sep}timeseries_cases.model', save_format="h5")
        final_data = {'prediction':week_cases, 'locale':locale}
        with open(f'.{os.sep}shr-data{os.sep}cache_cases.pckl', 'wb') as f:
            pickle.dump(final_data, f)
        return final_data


    def get_response(self):
        return self.response


if __name__ == '__main__':
    TimeSeriesLSTM(f_model_creation=True)