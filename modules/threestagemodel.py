import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class ThreeStageModel(object):

    """
    Paremeters
    ==========
    dict_of_kpi : dict with list of length 3: keys: 'a', 'g', 'p'
    list of periods: example - [0, 5, 10]


    """

    def __init__(self, dict_of_kpi, list_of_periods, sales_period_0):

        self.kpi = dict_of_kpi
        self.periods = list_of_periods
        self.sales_0 = sales_period_0

    # Year	Sales	a	g	p	EBIAT	NOA 	FCF	g(FCF)	NPV(FCF)	NPV(FCF)VC

    @staticmethod
    def get_period(periods, i):

        p1, p2, p3 = periods[0], periods[1], periods[2]
        if i > p3 - 1:
            return 2
        elif i > p2 - 1:
            return 1
        else:
            return 0

    @staticmethod
    def get_kpi(period, kpi):  # needs only a number from get_period

        a = kpi['a'][period]
        p = kpi['p'][period]
        g = kpi['g'][period]

        return a, p, g

    def run_model(self, discount_rate, last_of_period):

        self.discount_rate = discount_rate

        # initializing lists
        year = []
        sales = [self.sales_0]
        a_list = []
        g_list = []
        p_list = []
        EBIAT = []
        NOA = []
        FCF = [0]
        NPV_FCF = [0]
        CUM_NPV_FCF = []

        # Variables for model
        periods = self.periods
        kpi = self.kpi
        for i in range(last_of_period):

            period = self.get_period(periods, i)
            a, p, g = self.get_kpi(period, kpi)

            if i > 0:
                last_sales = sales[i - 1]
                sales.append(last_sales * (1 + g))

            sale = sales[i]

            a_list.append(a)
            p_list.append(p)
            g_list.append(g)
            year.append(i)
            NOA.append(sale * a)
            EBIAT.append(sale * p)

            if i > 0:
                FCF.append(EBIAT[i] - (NOA[i] - NOA[i - 1]))

                NPV_FCF.append(FCF[i] / ((1 + discount_rate)**(i)))

            CUM_NPV_FCF.append(np.sum(NPV_FCF))

        list_for_df = [a_list, p_list, g_list, NOA, year, EBIAT, FCF, NPV_FCF, sales, CUM_NPV_FCF]
        cols_for_df = ['a', 'p', 'g', 'NOA', 'year', 'EBIAT',
                       'FCF', 'NPV FCF', 'sales', 'cum NPV FCF']
        dict_for_df = {}
        for i in range(len(list_for_df)):
            dict_for_df[cols_for_df[i]] = list_for_df[i]

        df = pd.DataFrame(dict_for_df).round(decimals=2)
        df = df[['year', 'sales', 'g', 'a', 'p', 'EBIAT',
                 'NOA', 'FCF', 'NPV FCF', 'cum NPV FCF']]
        self.three_stage_model_df = df
        return df

    def latex_output(self):

        df = self.three_stage_model_df
        print(df.drop(['EBIAT', 'NOA'], axis=1).to_latex())

    def FCF_growth(self):
        df = self.three_stage_model_df
        FCF = list(df['FCF'])
        year = df['year']

        gFCF = [0]
        for i in range(len(FCF)):
            if i > 0:
                if FCF[i - 1] == 0:
                    gFCF.append(0)
                else:
                    e = (FCF[i] / FCF[i - 1]) - 1
                    gFCF.append(e)

        return gFCF

    # simulateAssetIntensity And SimulateGrowth Should be made to one method
    @classmethod
    def SimulateAssetIntensity(cls, low_bound=-0.2, high_bound=0.2):
        """
        Parameters
        ==========
        low_bound = (float) lower bound of delta parameter
        high_bound = (float) high bound of delta parameter

        Returns
        =======
        ai5, ai10, asset_intensity
        """

        asset_intensity = np.linspace(low_bound, high_bound)

        c5_list = []
        c10_list = []

        for i in asset_intensity:
            l = [0, 5, 10]
            d = {'a': [-0.15 + i, - 0.15 + i, -0.15 + i],
                 'p': [-0.15, 0.04, 0.08], 'g': [0.657, 0.4, 0.03]}
            s = 3.314

            m = cls(d, l, s)
            df = m.run_model(0.1, 16)

            c5_list.append(list(df['cum NPV FCF'])[5])
            c10_list.append((df['cum NPV FCF'])[10])

        return c5_list, c10_list, asset_intensity

    @classmethod
    def SimulateGrowth(cls, low_bound=-0.2, high_bound=0.2):
        """
        Parameters
        ==========
        low_bound = (float) lower bound of delta parameter
        high_bound = (float) high bound of delta parameter

        Returns
        =======
        gi5, gi10, asset_intensity
        """

        growth = np.linspace(low_bound, high_bound)

        c5_list = []
        c10_list = []

        for i in growth:
            l = [0, 5, 10]
            d = {'a': [-0.15, - 0.15, -0.15], 'p': [-0.15, 0.04, 0.08],
                 'g': [0.657 + i, 0.4 + i, 0.03 + i]}
            s = 3.314

            m = cls(d, l, s)
            df = m.run_model(0.1, 16)

            c5_list.append(list(df['cum NPV FCF'])[5])
            c10_list.append((df['cum NPV FCF'])[10])

        return c5_list, c10_list, growth

    def enterprise_value(self, period_for_gordons_formula):
        """
        Enterprise value

        Parameters
        =========
        period_for_gordons_formula (int) : The period at which gordons formula will be applied

        """

        gFCF = self.FCF_growth()
        df = self.three_stage_model_df

        # variables for price
        dividend = list(df['NPV FCF'])[period_for_gordons_formula]
        growth_in_dividends = gFCF[period_for_gordons_formula]
        required_rate_of_return = self.discount_rate
        price = dividend / (required_rate_of_return - growth_in_dividends)

        # variables for cum_FCF
        cum_ev = list(df['cum NPV FCF'])[period_for_gordons_formula - 1]

        print('the price is (gordons formula):', price)
        print('the cumulative value of firm is:', cum_ev)
        print('the sum of these components is:')

        return price + cum_ev

# %%
