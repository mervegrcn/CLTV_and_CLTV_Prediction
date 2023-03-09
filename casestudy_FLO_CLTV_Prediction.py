##############################################################
# BG-NBD ve Gamma-Gamma ile CLTV Prediction
##############################################################

###############################################################
# İş Problemi (Business Problem)
###############################################################
# FLO satış ve pazarlama faaliyetleri için roadmap belirlemek istemektedir.
# Şirketin orta uzun vadeli plan yapabilmesi için var olan müşterilerin gelecekte şirkete sağlayacakları potansiyel değerin tahmin edilmesi gerekmektedir.


###############################################################
# Veri Seti Hikayesi
###############################################################

# Veri seti son alışverişlerini 2020 - 2021 yıllarında OmniChannel(hem online hem offline alışveriş yapan) olarak yapan müşterilerin geçmiş alışveriş davranışlarından
# elde edilen bilgilerden oluşmaktadır.

# master_id: Eşsiz müşteri numarası
# order_channel : Alışveriş yapılan platforma ait hangi kanalın kullanıldığı (Android, ios, Desktop, Mobile, Offline)
# last_order_channel : En son alışverişin yapıldığı kanal
# first_order_date : Müşterinin yaptığı ilk alışveriş tarihi
# last_order_date : Müşterinin yaptığı son alışveriş tarihi
# last_order_date_online : Muşterinin online platformda yaptığı son alışveriş tarihi
# last_order_date_offline : Muşterinin offline platformda yaptığı son alışveriş tarihi
# order_num_total_ever_online : Müşterinin online platformda yaptığı toplam alışveriş sayısı
# order_num_total_ever_offline : Müşterinin offline'da yaptığı toplam alışveriş sayısı
# customer_value_total_ever_offline : Müşterinin offline alışverişlerinde ödediği toplam ücret
# customer_value_total_ever_online : Müşterinin online alışverişlerinde ödediği toplam ücret
# interested_in_categories_12 : Müşterinin son 12 ayda alışveriş yaptığı kategorilerin listesi


###############################################################
# GÖREVLER
###############################################################

###############################################################
# GÖREV 1: Veriyi Hazırlama
###############################################################

# 1. OmniChannel.csv verisini okuyunuz.Dataframe’in kopyasını oluşturunuz.

import datetime as dt
import pandas as pd
pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

df_ = pd.read_csv('/Users/mervegurcan/PycharmProjects/pythonProject/DATASETS/flo_data_20k.csv')
df = df_.copy()
df.isnull().sum()
df.dtypes


# 2. Aykırı değerleri baskılamak için gerekli olan outlier_thresholds ve replace_with_thresholds fonksiyonlarını tanımlayınız.
# Not: cltv hesaplanırken frequency değerleri integer olması gerekmektedir.Bu nedenle alt ve üst limitlerini round() ile yuvarlayınız.

df.describe().T

quartile1 = df.quantile(0.01)
quartile3 = df.quantile(0.99)

interquartile_range = quartile3 - quartile1

up_limit = quartile3 + 1.5 * interquartile_range
low_limit = quartile3 - 1.5 * interquartile_range

#Aykiri degerlerle oynamadan once describe fonk. ile veriyi incelemeliyiz. Aykiri deger var mi diye inceleme yapiyoruz
list = ["order_num_total_ever_online", "order_num_total_ever_offline", "customer_value_total_ever_offline", "customer_value_total_ever_online"]

for i in list:
    print(i,"değişkeninin threshold değerleri (low-up)" ,outlier_thresholds(df,i))

df[list].describe().T

def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range #ust esik degeri tanimlama
    low_limit = quartile1 - 1.5 * interquantile_range #alt esik degeri tanimlama

    return low_limit.round(), up_limit.round()


# alt ve üst limitleri geçen değerleri yakala, bunların yerine yukarıdaki up_limit, low_limit değerlerini yerleştir.
def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit

# 3. "order_num_total_ever_online","order_num_total_ever_offline","customer_value_total_ever_offline","customer_value_total_ever_online" değişkenlerinin
#aykırı değerleri varsa baskılayanız.

columns = ["order_num_total_ever_online","order_num_total_ever_offline","customer_value_total_ever_offline","customer_value_total_ever_online"]

outlier_thresholds(df, columns)

df.describe().T

for col in columns:
    replace_with_thresholds(df, col)

# 4. Omnichannel müşterilerin hem online'dan hemde offline platformlardan alışveriş yaptığını ifade etmektedir.
# Herbir müşterinin toplam alışveriş sayısı ve harcaması için yeni değişkenler oluşturun.

df.head()
df["order_num_total"] = df["order_num_total_ever_online"] + df["order_num_total_ever_offline"]
df["customer_value_total"] = df["customer_value_total_ever_offline"] + df["customer_value_total_ever_online"]


# 5. Değişken tiplerini inceleyiniz. Tarih ifade eden değişkenlerin tipini date'e çeviriniz.

df.dtypes

date_cols = [col for col in df.columns if 'date' in col]
for col in date_cols:
    df[col] = pd.to_datetime(df[col])

#LIST COMP.
#1
date_cols = [col for col in df.columns if str(col).__contains__("date")]
df[date_cols] = df[date_cols].apply(pd.to_datetime)

#2
[i for i in df.columns if "date" in i]
df[date_cols] = df[date_cols].apply(pd.to_datetime)
###############################################################
# GÖREV 2: CLTV Veri Yapısının Oluşturulması
###############################################################

# 1.Veri setindeki en son alışverişin yapıldığı tarihten 2 gün sonrasını analiz tarihi olarak alınız.

df["last_order_date"].max()

analysis_date = dt.datetime(2021, 6, 1)

# 2.customer_id, recency_cltv_weekly, T_weekly, frequency ve monetary_cltv_avg değerlerinin yer aldığı yeni bir cltv dataframe'i oluşturunuz.

cltv_df = pd.DataFrame()

cltv_df["customer_id"] = df["master_id"]

cltv_df["recency_cltv_weekly"] = ((df["last_order_date"] - df["first_order_date"]).astype('timedelta64[D]')) / 7

cltv_df["T_weekly"] = (analysis_date - df["first_order_date"]).astype('timedelta64[D]') / 7

cltv_df["frequency"] = df["order_num_total"]

cltv_df["monetary_cltv_avg"] = df["customer_value_total"] / df["order_num_total"]

cltv_df = cltv_df[(cltv_df['frequency'] > 1)]

###############################################################
# GÖREV 3: BG/NBD, Gamma-Gamma Modellerinin Kurulması, 6 aylık CLTV'nin hesaplanması
###############################################################

# 1. BG/NBD modelini kurunuz.

from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter
from lifetimes.plotting import plot_period_transactions

bgf = BetaGeoFitter(penalizer_coef=0.001)
bgf.fit(cltv_df['frequency'],
        cltv_df['recency_cltv_weekly'],
        cltv_df['T_weekly'])

# 3 ay içerisinde müşterilerden beklenen satın almaları tahmin ediniz ve exp_sales_3_month olarak cltv dataframe'ine ekleyiniz.

cltv_df["exp_sales_3_month"] = bgf.predict(4 * 3,
                                           cltv_df['frequency'],
                                           cltv_df['recency_cltv_weekly'],
                                           cltv_df['T_weekly'])

# 6 ay içerisinde müşterilerden beklenen satın almaları tahmin ediniz ve exp_sales_6_month olarak cltv dataframe'ine ekleyiniz.

cltv_df["exp_sales_6_month"] = bgf.predict(4 * 6,
                                           cltv_df['frequency'],
                                           cltv_df['recency_cltv_weekly'],
                                           cltv_df['T_weekly'])


# 3. ve 6.aydaki en çok satın alım gerçekleştirecek 10 kişiyi inceleyeniz.

cltv_df["exp_sales_3_month"].head(10)
cltv_df["exp_sales_6_month"].head(10)


# 2.  Gamma-Gamma modelini fit ediniz. Müşterilerin ortalama bırakacakları değeri tahminleyip exp_average_value olarak cltv dataframe'ine ekleyiniz.

ggf = GammaGammaFitter(penalizer_coef=0.01)

ggf.fit(cltv_df['frequency'], cltv_df['monetary_cltv_avg'])

cltv_df["exp_average_value"] = ggf.conditional_expected_average_profit(cltv_df['frequency'],
                                                                       cltv_df['monetary_cltv_avg'])

# 3. 6 aylık CLTV hesaplayınız ve cltv ismiyle dataframe'e ekleyiniz.

cltv = ggf.customer_lifetime_value(bgf, #transaction prediction model
                                   cltv_df['frequency'],
                                   cltv_df['recency_cltv_weekly'],
                                   cltv_df['T_weekly'],
                                   cltv_df['monetary_cltv_avg'],
                                   time=6,
                                   freq="W", #week demek. bgf hesbai weekly oldugu icin
                                   discount_rate=0.01)

cltv_df["cltv"] = cltv

# CLTV değeri en yüksek 20 kişiyi gözlemleyiniz.

cltv_df.sort_values(by="cltv", ascending=False).head(20)

###############################################################
# GÖREV 4: CLTV'ye Göre Segmentlerin Oluşturulması
###############################################################

# 1. 6 aylık CLTV'ye göre tüm müşterilerinizi 4 gruba (segmente) ayırınız ve grup isimlerini veri setine ekleyiniz.
# cltv_segment ismi ile atayınız.

cltv_df["cltv_segment"] = pd.qcut(cltv_df["cltv"], 4, labels=["D", "C", "B", "A"])


# 2. Segmentlerin recency, frequnecy ve monetary ortalamalarını inceleyiniz.

cltv_df.groupby("cltv_segment").agg({"recency_cltv_weekly":"mean",
                                     "frequency":"mean",
                                     "monetary_cltv_avg":"mean"})

###############################################################
# BONUS: Tüm süreci fonksiyonlaştırınız.
###############################################################

def create_cltv_df(dataframe):

    # Veriyi Hazırlama
    columns = ["order_num_total_ever_online", "order_num_total_ever_offline", "customer_value_total_ever_offline","customer_value_total_ever_online"]
    for col in columns:
        replace_with_thresholds(dataframe, col)

    dataframe["order_num_total"] = dataframe["order_num_total_ever_online"] + dataframe["order_num_total_ever_offline"]
    dataframe["customer_value_total"] = dataframe["customer_value_total_ever_offline"] + dataframe["customer_value_total_ever_online"]
    dataframe = dataframe[~(dataframe["customer_value_total"] == 0) | (dataframe["order_num_total"] == 0)]
    date_columns = dataframe.columns[dataframe.columns.str.contains("date")]
    dataframe[date_columns] = dataframe[date_columns].apply(pd.to_datetime)

    # CLTV veri yapısının oluşturulması
    dataframe["last_order_date"].max()  # 2021-05-30
    analysis_date = dt.datetime(2021, 6, 1)
    cltv_df = pd.DataFrame()
    cltv_df["customer_id"] = dataframe["master_id"]
    cltv_df["recency_cltv_weekly"] = ((dataframe["last_order_date"] - dataframe["first_order_date"]).astype('timedelta64[D]')) / 7
    cltv_df["T_weekly"] = ((analysis_date - dataframe["first_order_date"]).astype('timedelta64[D]')) / 7
    cltv_df["frequency"] = dataframe["order_num_total"]
    cltv_df["monetary_cltv_avg"] = dataframe["customer_value_total"] / dataframe["order_num_total"]
    cltv_df = cltv_df[(cltv_df['frequency'] > 1)]

    # BG-NBD Modelinin Kurulması
    bgf = BetaGeoFitter(penalizer_coef=0.001)
    bgf.fit(cltv_df['frequency'],
            cltv_df['recency_cltv_weekly'],
            cltv_df['T_weekly'])
    cltv_df["exp_sales_3_month"] = bgf.predict(4 * 3,
                                               cltv_df['frequency'],
                                               cltv_df['recency_cltv_weekly'],
                                               cltv_df['T_weekly'])
    cltv_df["exp_sales_6_month"] = bgf.predict(4 * 6,
                                               cltv_df['frequency'],
                                               cltv_df['recency_cltv_weekly'],
                                               cltv_df['T_weekly'])

    # # Gamma-Gamma Modelinin Kurulması
    ggf = GammaGammaFitter(penalizer_coef=0.01)
    ggf.fit(cltv_df['frequency'], cltv_df['monetary_cltv_avg'])
    cltv_df["exp_average_value"] = ggf.conditional_expected_average_profit(cltv_df['frequency'],
                                                                           cltv_df['monetary_cltv_avg'])

    # Cltv tahmini
    cltv = ggf.customer_lifetime_value(bgf,
                                       cltv_df['frequency'],
                                       cltv_df['recency_cltv_weekly'],
                                       cltv_df['T_weekly'],
                                       cltv_df['monetary_cltv_avg'],
                                       time=6,
                                       freq="W",
                                       discount_rate=0.01)
    cltv_df["cltv"] = cltv

    # CLTV segmentleme
    cltv_df["cltv_segment"] = pd.qcut(cltv_df["cltv"], 4, labels=["D", "C", "B", "A"])

    return cltv_df

cltv_df = create_cltv_df(df)


cltv_df.head(10)


# 4 grup içerisinden seçeceğiniz 2 grup için yönetime kısa kısa 6 aylık aksiyon önerilerinde bulununuz.