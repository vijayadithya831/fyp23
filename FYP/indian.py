# -*- coding: utf-8 -*-
"""Indian.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MS8gfNT-qMuEQl6IEi5RPY_bdKWoOg5d
"""
def ret():
        import numpy as np
        import pandas as pd
        import geopandas as gpd
        import matplotlib.pyplot as plt
        import warnings
        import copy
        warnings.simplefilter("ignore")
        plt.style.use("bmh")
        from keras.metrics.metrics import mean_squared_error

        df = pd.read_csv('myvalues.csv')

        df.head()

        df['DateTime']=pd.to_datetime(df['DateTime'])

        df['Date'] = df.DateTime.dt.date
        df['Time'] = df.DateTime.dt.time

        df["Date"] = df["Date"].astype("object")
        for i, date_str in enumerate(df["Date"].unique()):
            df.loc[df["Date"]==date_str, "Date"] = f"{str(date_str)[0:4]}-{str(date_str)[4:6]}-{str(date_str)[6:]}"

        print(f"Dataset contains data of {df['CycloneName'].unique().shape[0]} individual storms from {df['DateTime'].dt.year.min()} to {df['DateTime'].dt.year.max()}.")

        def coordinate_mapping(x):
            coord = float(x[:-1])
            if x[-1]=="W":
                coord *= -1
            if x[-1]=="S":
                coord *= -1
            return coord

        print("Min. Long.:", df.Longitude.min(), "Max. Long.:", df.Longitude.max(), "Min. Lat.:", df.Latitude.min(), "Max. Lat.:", df.Latitude.max())

        df.loc[df.Longitude<-180, "Longitude"] = df.Longitude+360

        gdf = gpd.GeoDataFrame(df,geometry=gpd.points_from_xy(df.Longitude,df.Latitude), crs={'init' : 'epsg:4326'})

        gdf.crs

        world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))

        name = gdf["CycloneName"]

        ax = world.plot(color="white", edgecolor="black", figsize=(25,12))
        _ = gdf[gdf["CycloneName"]==name].plot(ax=ax, c="r", markersize="Maximum Wind", alpha=0.5)
        _ = plt.xlim(50, 100)
        _ = plt.ylim(0, 50)

        gdf.head()

        lat_min = gdf.Latitude.min()
        long_min = gdf.Longitude.min()
        gdf["x"] = gdf.Latitude-lat_min
        gdf["x"] = gdf["x"]/gdf["x"].max()
        gdf["y"] = gdf.Longitude-long_min
        gdf["y"] = gdf["y"]/gdf["y"].max()

        gdf.head()

        gdf["relative_time"] = ((gdf.DateTime.dt.dayofyear+(gdf.DateTime.dt.hour/24.)+(gdf.DateTime.dt.minute/60.*24))/366.)

        gdf["month"] = gdf.DateTime.dt.month
        gdf["hour"] = gdf.DateTime.dt.hour

        _ = gdf.plot(x="relative_time", y="Maximum Wind", kind="scatter", figsize=(20,12), title="Max. Wind vs. relative_time")
        _ = plt.ylim(0,180)
        _ = plt.xlim(0,1)

        df.head()

        gdf["vec_x"] = np.nan
        gdf["vec_y"] = np.nan
        vecs = {"x": [], "y": [], "id": []}
        for storm_id in gdf["CycloneName"].unique():
            last_x = 0
            last_y = 0
            for i, row in gdf[gdf["CycloneName"]==storm_id].iterrows():
                if last_x==0:
                    last_x = row.x
                    last_y = row.y
                else:
                    vec_x = row.x-last_x
                    vec_y = row.y-last_y
                    vecs["x"].append(vec_x)
                    vecs["y"].append(vec_y)
                    vecs["id"].append(i)
                    last_x = row.x
                    last_y = row.y
        gdf.loc[vecs["id"], "vec_x"] = vecs["x"]
        gdf.loc[vecs["id"], "vec_y"] = vecs["y"]

        gdf.head()

        gdf["vec_len"] = np.sqrt((gdf["vec_x"]**2)+(gdf["vec_y"]**2))

        def calculate_direction(vec_x, vec_y):
            def vec_angle(a, b):
                return np.arccos(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
            ref_vec = np.array([vec_x, vec_y])
            N_vec = np.array([0,1])
            S_vec = np.array([0,-1])
            E_vec = np.array([1,0])
            W_vec = np.array([-1,0])
            N_angle = vec_angle(ref_vec, N_vec)
            E_angle = vec_angle(ref_vec, E_vec)
            W_angle = vec_angle(ref_vec, W_vec)
            return_angle = N_angle
            if W_angle<E_angle:
                return_angle = 2*np.pi-return_angle
            return return_angle

        gdf["vec_direction"] = gdf.apply(lambda x: calculate_direction(x.vec_x, x.vec_y), axis=1)

        gdf["tdelta"] = np.nan
        tdeltas = {"t": [], "id": []}
        for storm_id in gdf["CycloneName"].unique():
            last_time = 0
            for i, row in gdf[gdf["CycloneName"]==storm_id].iterrows():
                if last_time==0:
                    last_time = row.DateTime
                else:
                    tdeltas["t"].append((row.DateTime-last_time).seconds)
                    tdeltas["id"].append(i)
                    last_time = row.DateTime
        gdf.loc[tdeltas["id"], "tdelta"] = tdeltas["t"]

        gdf.head()

        gdf = gdf[gdf["tdelta"]==21600]
        gdf.shape

        gdf["prev_len"] = np.nan
        gdf["prev_direction"] = np.nan
        prevs = {"len": [], "direction": [], "id": []}
        for storm_id in gdf["CycloneName"].unique():
            last_len = False
            last_direction = False
            for i, row in gdf[gdf["CycloneName"]==storm_id].iterrows():
                if last_len==False:
                    last_len = row.vec_len
                    last_direction = row.vec_direction
                else:
                    prevs["len"].append(last_len)
                    prevs["direction"].append(last_direction)
                    prevs["id"].append(i)
                    last_len = row.vec_len
                    last_direction = row.vec_direction
        gdf.loc[prevs["id"], "prev_len"] = prevs["len"]
        gdf.loc[prevs["id"], "prev_direction"] = prevs["direction"]

        gdf.dropna(how="any", inplace=True)
        gdf.shape

        """Prediction"""

        gdf_prediction_direction = gdf[["Maximum Wind", "x", "y", "month", "hour", "prev_len", "prev_direction", "vec_direction"]]
        gdf_prediction_length = gdf[["Maximum Wind", "x", "y", "month", "hour", "prev_len", "prev_direction","vec_len"]]
        X_direction = gdf_prediction_direction.values[:,:-1]
        y_direction = gdf_prediction_direction.values[:,-1]
        X_length = gdf_prediction_length.values[:,:-1]
        y_length = gdf_prediction_length.values[:,-1]

        gdf.head()

        from sklearn.model_selection import train_test_split
        X_direction_train, X_direction_test, y_direction_train, y_direction_test = train_test_split(X_direction, y_direction, test_size=0.2, random_state=42)
        X_length_train, X_length_test, y_length_train, y_length_test = train_test_split(X_length, y_length, test_size=0.2, random_state=42)

        print(X_direction.shape)
        print(y_direction.shape)
        print(X_length.shape)
        print(y_length.shape)

        """LSTM

        """

        from sklearn.preprocessing import MinMaxScaler
        from sklearn.preprocessing import StandardScaler
        from keras.models import Sequential
        from keras.layers.core import Dense, Dropout, Activation
        from keras.layers import LSTM
        import math, time
        from geopy.distance import great_circle as vc
        import math as Math
        from keras.models import model_from_json

        # Define the number of inputs, hidden units, and outputs
        n_inputs = X_direction_train.shape[1]
        n_hidden1 = 100
        n_hidden2 = 50
        n_hidden3 = 25
        n_outputs = 1

        # Create the LSTM model
        model = Sequential()
        model.add(LSTM(n_hidden1, input_shape=(n_inputs, 1), return_sequences=True))
        model.add(LSTM(n_hidden2, return_sequences=True))
        model.add(LSTM(n_hidden3))
        model.add(Dense(n_outputs))

        # Compile the model
        model.compile(loss='mean_squared_error', optimizer='adam')

        # Train the model
        model_direction_lstm = model.fit(X_direction_train, y_direction_train, epochs=100, batch_size=64)

        model1 = Sequential()
        model1.add(LSTM(n_hidden1, input_shape=(n_inputs, 1), return_sequences=True))
        model1.add(LSTM(n_hidden2, return_sequences=True))
        model1.add(LSTM(n_hidden3))
        model1.add(Dense(n_outputs))

        # Compile the model
        model1.compile(loss='mean_squared_error', optimizer='adam')

        # Train the model
        model_length_lstm = model1.fit(X_length_train, y_length_train, epochs=100, batch_size=64)

        Y_test_predicted_lstm_direction = model.predict(X_direction_test)
        # print(Y_test_predicted_lstm_direction)
        Y_test_predicted_lstm_length = model1.predict(X_length_test)
        # print(Y_test_predicted_lstm_length)
        predicted = np.dstack((Y_test_predicted_lstm_direction,Y_test_predicted_lstm_length))
        print(predicted)

        errorlstm = mean_squared_error(y_direction_test,Y_test_predicted_lstm_direction[:,0]).numpy()
        print(errorlstm)
        lstm = [Y_test_predicted_lstm_direction,Y_test_predicted_lstm_length,errorlstm]

        mean_squared_error(y_length_test,Y_test_predicted_lstm_length[:,0])

        """MLP"""

        from sklearn.neural_network import MLPRegressor
        mlp = MLPRegressor(hidden_layer_sizes=100,learning_rate_init=0.1,max_iter=300,verbose=True)
        mlp1 = MLPRegressor(hidden_layer_sizes=100,learning_rate_init=0.1,max_iter=300,verbose=True)

        model_direction_mlp = mlp.fit(X_direction_train, y_direction_train)

        model_length_mlp = mlp1.fit(X_length_train, y_length_train)

        Y_test_predicted_mlp_direction = mlp.predict(X_direction_test)
        Y_test_predicted_mlp_length = mlp1.predict(X_length_test)

        errormlp = mean_squared_error(y_direction_test,Y_test_predicted_mlp_direction).numpy()
        print(errormlp)
        mlp = [model_direction_mlp,model_length_mlp,errormlp]

        mean_squared_error(y_length_test,Y_test_predicted_mlp_length)

        """GradientBoostingRegressor"""

        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.metrics import mean_squared_error

        model_direction = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=0).fit(X_direction_train, y_direction_train)
        errorgrad = mean_squared_error(y_direction_test, model_direction.predict(X_direction_test))
        print(errorgrad)

        model_length = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=0,).fit(X_length_train, y_length_train)
        mean_squared_error(y_length_test, model_length.predict(X_length_test))
        grad = [model_direction,model_length,errorgrad]
        print(grad[0],grad[1])

        print(grad[1])

        """SVR"""

        from sklearn.svm import SVR
        svr = SVR(kernel='rbf',C=1.0,epsilon=0.1,degree=3)
        svr1 = SVR(kernel='rbf',C=1.0,epsilon=0.1,degree=3)

        model_direction_svr = svr.fit(X_direction_train, y_direction_train)
        model_length_svr = svr1.fit(X_length_train, y_length_train)

        Y_test_direction_predicted_svr = model_direction_svr.predict(X_direction_test)
        Y_test_length_predicted_svr = model_length_svr.predict(X_length_test)

        errorsvr = mean_squared_error(y_direction_test,Y_test_direction_predicted_svr)
        print(errorsvr)
        svr = [model_direction_svr,model_length_svr,errorsvr]

        mean_squared_error(y_length_test,Y_test_length_predicted_svr)

        """LinearRegression"""

        from sklearn.linear_model import LinearRegression
        lin_reg = LinearRegression(fit_intercept=True, copy_X=True, n_jobs=1)
        lin_reg1 = LinearRegression(fit_intercept=True, copy_X=True, n_jobs=1)

        model_direction_lr = lin_reg.fit(X_direction_train, y_direction_train)
        model_length_lr = lin_reg1.fit(X_length_test,y_length_test)

        Y_test_direction_predicted_lr = model_direction_lr.predict(X_direction_test)
        Y_test_length_predicted_lr = model_length_lr.predict(X_length_test)
        print(Y_test_direction_predicted_lr,Y_test_length_predicted_lr)

        errorlr = mean_squared_error(y_direction_test,Y_test_direction_predicted_lr)
        print(errorlr)
        lr = [model_direction_lr,model_length_lr,errorlr]

        mean_squared_error(y_length_test,Y_test_length_predicted_lr)

        predvals = [errorlstm,errormlp,errorgrad,errorsvr,errorlr]
        print(predvals)

        minerror = min(predvals)
        print(minerror)

        if minerror==errorlstm:
            model_direction = lstm[0]
            model_length = lstm[1]
        elif minerror==errormlp:
            model_direction = mlp[0]
            model_length = mlp[1]
        elif minerror==errorsvr:
            model_direction = svr[0]
            model_length = svr[1]
        elif minerror==errorlr:
            model_direction = lr[0]
            model_length = lr[1]

        lat_min = df.Latitude.min()
        long_min = df.Longitude.min()
        temp_x = df.Latitude-lat_min
        temp_y = df.Longitude-long_min
        x_max = temp_x.max()
        y_max = temp_y.max()

        def coords_to_latlong(x, y, lat_min, long_min, x_max, y_max):
            return (x*x_max)+lat_min, (y*y_max)+long_min

        gdf_pred = gdf[["Latitude", "Longitude", "Maximum Wind", "x", "y", "month", "hour", "prev_len", "prev_direction", "vec_len", "vec_direction"]][gdf.CycloneName==name[0]]
        X_pred_direction = gdf_pred[["Maximum Wind", "x", "y", "month", "hour", "prev_len", "prev_direction"]].iloc[1:].values
        X_pred_len = gdf_pred[["Maximum Wind", "x", "y", "month", "hour", "prev_len", "prev_direction"]].iloc[1:].values

        df_pred = pd.DataFrame({"pred_len": model_length.predict(X_pred_len), "pred_direction": model_direction.predict(X_pred_direction)})

        df_pred["pred_x"] = np.nan
        df_pred["pred_y"] = np.nan
        df_pred["real_x"] = gdf_pred["x"].iloc[1:].values
        df_pred["real_y"] = gdf_pred["y"].iloc[1:].values

        last_x = gdf_pred["x"].iloc[0]
        last_y = gdf_pred["y"].iloc[0]
        coords = {"x": [], "y": [], "id": []}
        for i, row in df_pred.iterrows():
            vector = np.array([0,1])
            R = np.array([[np.cos(row.pred_direction), -np.sin(row.pred_direction)], [np.sin(row.pred_direction), np.cos(row.pred_direction)]])
            vector = np.matmul(vector, R)
            vector = vector/np.linalg.norm(vector)
            vector *= row.pred_len
            coords["x"].append(last_x+vector[0])
            coords["y"].append(last_y+vector[1])
            coords["id"].append(i)
            last_x = row.real_x
            last_y = row.real_y
        df_pred.loc[coords["id"], "pred_x"] = coords["x"]
        df_pred.loc[coords["id"], "pred_y"] = coords["y"]

        df_pred["pred_Longitude"] = np.nan
        df_pred["real_Longitude"] = np.nan
        df_pred["pred_Latitude"] = np.nan
        df_pred["real_Latitude"] = np.nan
        latslongs = {"pred_Longitude": [], "real_Longitude": [], "pred_Latitude": [], "real_Latitude": [], "id": []}
        for i, row in df_pred.iterrows():
            real_Latitude, real_Longitude = coords_to_latlong(row.real_x, row.real_y, lat_min, long_min, x_max, y_max)
            latslongs["real_Latitude"].append(real_Latitude)
            latslongs["real_Longitude"].append(real_Longitude)
            pred_Latitude, pred_Longitude = coords_to_latlong(row.pred_x, row.pred_y, lat_min, long_min, x_max, y_max)
            latslongs["pred_Latitude"].append(pred_Latitude)
            latslongs["pred_Longitude"].append(pred_Longitude)
            latslongs["id"].append(i)
        df_pred.loc[latslongs["id"], "real_Latitude"] = latslongs["real_Latitude"]
        df_pred.loc[latslongs["id"], "real_Longitude"] = latslongs["real_Longitude"]
        df_pred.loc[latslongs["id"], "pred_Latitude"] = latslongs["pred_Latitude"]
        df_pred.loc[latslongs["id"], "pred_Longitude"] = latslongs["pred_Longitude"]

        gdf_real = gpd.GeoDataFrame(df_pred,geometry=gpd.points_from_xy(df_pred.real_Longitude,df_pred.real_Latitude), crs={'init' :'epsg:4326'})
        gdf_pred = gpd.GeoDataFrame(df_pred,geometry=gpd.points_from_xy(df_pred.pred_Longitude,df_pred.pred_Latitude), crs={'init' :'epsg:4326'})

        ax = world.plot(color="white", edgecolor="black", figsize=(25,20))
        _ = gdf_real.plot(ax=ax, c="r", marker="x", alpha=0.5)
        _ = gdf_pred.plot(ax=ax, c="b", marker="x", alpha=0.5)
        _ = plt.xlim(-90, 0)
        _ = plt.ylim(0, 90)

        return gdf_pred['pred_Latitude'],gdf_pred['pred_Longitude'],name[0]