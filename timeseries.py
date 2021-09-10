from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from datetime import datetime, timedelta
from db_transactions import PsqlPy
import numpy as np
import os
import pickle
import pandas as pd
import yaml

class TimeSeriesLSTM:
    def __init__(self, f_model_creation:bool=False, day_check:str=None) -> None:
        """
        TimeSeriesLSTM class to generate prediction based on recent Covid-19 cases.

        Args:
            f_model_creation (bool, optional): [Forces a model recreation]. Defaults to False.
            day_check (str, optional): [Check if model is outdated]. Defaults to None.
        """
        self.url_repo = 'https://raw.githubusercontent.com/seade-R/dados-covid-sp/master/data/dados_covid_sp.csv'
        self.model_path = f'.{os.sep}shr-data{os.sep}cache_cases.pckl'
        self.look_back = 7
        self.crashed = False
        if self.crashed:
            print("Unavailable model!")
        elif f_model_creation:
            self.response = self.create_model()
        else:
            try:
                with open(self.model_path, 'rb') as f:
                    self.response = pickle.load(f)
                if day_check and (day_check != self.response.get('processed_date')):
                    db = PsqlPy()
                    db.reset_notif()
                    db.disconnect()
                    self.response = self.create_model()
            except Exception:
                # if os.path.exists(self.model_path):
                #     os.remove(self.model_path)
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
            for i in range(len(dataset)-look_back):
                dataX.append(dataset[i:(i+look_back), 0])
                dataY.append(dataset[i + look_back, 0])
            return np.array(dataX), np.array(dataY)

        df_cases = df_filtered[:]['casos_novos'].values.astype('float32')
        df_cases = df_cases.reshape(len(df_cases),1)

        # np.random.seed(7)
        # scalling data
        scaler = MinMaxScaler(feature_range=(0, 1))
        df_cases = scaler.fit_transform(df_cases)

        trainX, trainY = create_dataset(df_cases, self.look_back)
        trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))

        # modelling, compilling and fitting
        hidden_nodes = int(2/3 * self.look_back)
        model = Sequential()
        model.add(LSTM(hidden_nodes, input_shape=(1, self.look_back)))
        model.add(Dense(hidden_nodes*2))
        model.add(Dropout(0.0055))
        model.add(Dense(1, activation='tanh'))
        model.compile(loss='mean_squared_error', optimizer='adam')
        model.fit(trainX, trainY, epochs=30, batch_size=1, verbose=1)

        # last look_back cases
        look_back_cases = df_cases[-self.look_back:]
        # predict more cases (quantity based on look_back value)
        for _ in range(self.look_back):
            pred_day = model.predict(look_back_cases.reshape(1, 1, self.look_back))
            look_back_cases = np.append(look_back_cases,pred_day,axis=0)
            look_back_cases = np.delete(look_back_cases, 0, axis=0)

        # rescale predicted cases
        predicted_cases = scaler.inverse_transform(look_back_cases)
        # round them
        predicted_cases = np.round(predicted_cases).astype(int)
        # last week cases
        last_week_cases = scaler.inverse_transform(df_cases[-self.look_back:])
        # round them
        last_week_cases = np.round(last_week_cases).astype(int)
        # creating prediction dict, until now will only have last cases
        cases_prediction_dict = {day:[0, int(case)] for day, case in zip(df_filtered[-len(last_week_cases):]['datahora'], last_week_cases)}

        # verify if we already have today case
        current_date = datetime.now()
        if current_date.strftime("%Y-%m-%d") in cases_prediction_dict.keys():
            current_date += timedelta(days=1)
        else:
            predicted_cases = np.delete(predicted_cases, -1)

        # append predicted cases
        for predicted_case in predicted_cases:
            cases_prediction_dict[current_date.strftime("%Y-%m-%d")] = [1, int(predicted_case)]
            current_date += timedelta(days=1)

        #model.save(f'.{os.sep}shr-data{os.sep}timeseries_cases.model', save_format="h5")
        final_data = {'prediction':cases_prediction_dict, 'locale':locale, 'processed_date': datetime.now().strftime("%d/%m/%Y")}
        with open(self.model_path, 'wb') as f:
            pickle.dump(final_data, f)
        return final_data


    def get_response(self):
        return self.response


if __name__ == '__main__':
    TimeSeriesLSTM(f_model_creation=True)