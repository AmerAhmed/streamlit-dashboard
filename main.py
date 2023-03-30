"""
The module for streamlit dashboard.
Author: Amer Ahmed
Version 0.0
"""
import json
import time

import lxml
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import tldextract
from bs4 import BeautifulSoup
from streamlit_tags import st_tags


def display_scraper_result():
    """Display the results of a streamlit dashboard"""

    st.title(':bar_chart: Analysis Visualizer')
    df = pd.read_csv('./src/ad_scrape_result.csv')

    keywords = df['Keyword'].unique().tolist()
    keyword_selection = st.multiselect('Keyword:', keywords, default=keywords)

    if not keyword_selection:
        st.error("Please select at least one keyword to display the dataframe.")
    mask = df['Keyword'].isin(keyword_selection)
    number_of_result = df[mask].shape[0]
    st.markdown(f'*Available rows: {number_of_result}*')
    st.dataframe(df[mask])

    # st.dataframe(groupedKeywordPercentage_df)
    grouped_keyword_percentage_df = generate_keyword_ad_percentage(df)
    # remove rows with zero percentage
    grouped_keyword_percentage_df = grouped_keyword_percentage_df[
        grouped_keyword_percentage_df.Percentage != 0]

    # plot bar chart
    bar_chart = px.bar(
        grouped_keyword_percentage_df,
        x="Keyword",
        y="Percentage",
        text="Percentage",
        template="plotly_white",
        title="Keyword Ads Percentage(%)"
    )
    st.plotly_chart(bar_chart)

    test_df = df.groupby(by="Company", dropna=True)

    company_list = []
    company_count = []
    for key, _ in test_df:
        company_list.append(key)
        company_count.append(len(test_df.get_group(key)))

    company_appearance_df = pd.DataFrame({'Company': company_list, 'Appearance': company_count}, columns=[
        'Appearance'], index=company_list)
    st.dataframe(company_appearance_df)

    # show the company appearance
    st.bar_chart(company_appearance_df)

    for keyword in keywords:
        keyword_df = df[df['Keyword'] == keyword]
        if keyword_df['Company'] is not None:
            st.write(keyword)
            new_df = pd.DataFrame({'Company': keyword_df['Company'].tolist(),
                                   'absolute-top': keyword_df['absolute-top'].tolist(),
                                   'top': keyword_df['top'].tolist(),
                                   'bottom': keyword_df['bottom'].tolist()},
                                  columns=["absolute-top", "top", "bottom"],
                                  index=keyword_df['Company'].tolist())
            st.bar_chart(new_df)


# Generate Keyword Ads Appearance Percentage
def generate_keyword_ad_percentage(df):
    """Generate keyword ads appearance percentage"""
    keyword_ad_percentage = []
    for keyword in df['Keyword'].unique().tolist():
        if df[df['Keyword'] == keyword]['Keyword Ads Percentage(%)'].max() is None:
            keyword_ad_percentage.append(0)
        else:
            keyword_ad_percentage.append(
                df[df['Keyword'] == keyword]['Keyword Ads Percentage(%)'].max())

    grouped_keyword_percentage_df = pd.DataFrame(list(zip(df['Keyword'].unique(
    ).tolist(), keyword_ad_percentage)), columns=['Keyword', 'Percentage'])
    grouped_keyword_percentage_df = grouped_keyword_percentage_df.sort_values(
        by=['Percentage'], ascending=False)
    return grouped_keyword_percentage_df


def ad_scraper(number_of_times, list_of_keywords):
    """Returns a list of keywords ads for a given number of times"""
    # Specify User Agent
    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.87 Safari/537.36"
    }
    # progress bar for scraping
    st.subheader('Progress:')
    my_bar = st.progress(0)
    progress = 0

    result_dict = {}
    for keyword in list_of_keywords:
        company_list = []
        num_of_top_ads = 0
        num_of_bottom_ads = 0
        result_dict[keyword] = {}
        absolute_top = 0
        print(keyword)
        for i in range(number_of_times):
            payload = {'q': keyword}
            html = requests.get(
                "https://www.google.com/search?q=", params=payload, headers=headers)
            status_code = html.status_code

            if status_code == 200:
                response = html.text
                soup = BeautifulSoup(response, "lxml")
                print('----------------Top Ads-------------------')
                top_ads = soup.find(id='tvcap')
                if (top_ads):
                    if len(top_ads.findAll('div', class_='uEierd')) > 0:
                        num_of_top_ads += 1
                    absolute_top = 0
                    for container in top_ads.findAll('div', class_='uEierd'):
                        try:
                            advertisement_title = container.find(
                                'div', class_='CCgQ5 vCa9Yd QfkTvb MUxGbd v0nnCb').span.text
                        except:
                            advertisement_title = 'N/A'

                        company = container.find('div', class_='v5yQqb').find(
                            'span', class_='x2VHCd OSrXXb nMdasd qzEoUe').text
                        company = tldextract.extract(company).domain

                        if company not in company_list:
                            company_list.append(company)
                            if absolute_top == 0:
                                result_dict[keyword][company] = {
                                    'absolute-top': 1, 'top': 0, 'bottom': 0}
                            else:
                                result_dict[keyword][company] = {
                                    'absolute-top': 0, 'top': 1, 'bottom': 0}
                        else:
                            if absolute_top == 0:
                                result_dict[keyword][company]['absolute-top'] += 1
                            else:
                                result_dict[keyword][company]['top'] += 1

                        product_description = container.find(
                            'div', class_='MUxGbd yDYNvb lyLwlc').text

                        print(advertisement_title)
                        print(company)
                        print(product_description)
                        print()
                        absolute_top += 1
                    progress += (0.5 / (len(list_of_keywords)
                                 * number_of_times))
                    my_bar.progress(progress)

                time.sleep(0.05)
                print('------------------------------------------')
                print('----------------Bottom Ads-------------------')
                bottom_ads = soup.find(id='bottomads')
                if (bottom_ads):
                    if len(bottom_ads.findAll('div', class_='uEierd')) > 0:
                        num_of_bottom_ads += 1
                    for container in bottom_ads.findAll('div', class_='uEierd'):
                        try:
                            advertisement_title = container.find(
                                'div', class_='CCgQ5 vCa9Yd QfkTvb MUxGbd v0nnCb').span.text
                        except:
                            advertisement_title = 'N/A'

                        company = container.find('div', class_='v5yQqb').find(
                            'span', class_='x2VHCd OSrXXb nMdasd qzEoUe').text
                        company = tldextract.extract(company).domain

                        if company not in company_list:
                            company_list.append(company)
                            result_dict[keyword][company] = {
                                'absolute-top': 0, 'top': 0, 'bottom': 1}
                        else:
                            result_dict[keyword][company]['bottom'] += 1

                        product_description = container.find(
                            'div', class_='MUxGbd yDYNvb lyLwlc').text

                        print(advertisement_title)
                        print(company)
                        print(product_description)
                        print()
                    progress += (0.5 / (len(list_of_keywords)
                                 * number_of_times))
                    my_bar.progress(round(progress, 1))

        keys = list(result_dict[keyword].keys())
        for name in ['bottom', 'top', 'absolute-top']:
            keys.sort(
                key=lambda k: result_dict[keyword][k][name], reverse=True)

        result_dict[keyword]['top performers'] = keys
        result_dict[keyword]['total top ads'] = num_of_top_ads
        result_dict[keyword]['total bottom ads'] = num_of_bottom_ads

    print(json.dumps(result_dict, indent=4))
    # print success message
    st.success('Google Ads Scraping completed successfully.')
    return result_dict


def json_to_data_frame(result_dict, list_of_keywords):
    """Converts a list of keywords to a json object with dataframe representation"""
    result_list = []
    for keyword in list_of_keywords:
        if result_dict[keyword]["top performers"] != []:
            for company in result_dict[keyword]["top performers"]:
                top_percentage = 0
                bottom_percentage = 0
                if result_dict[keyword]["total top ads"] != 0:
                    top_percentage = round((result_dict[keyword][company]["top"] + result_dict[keyword]
                                            [company]["absolute-top"]) / result_dict[keyword]["total top ads"] * 100, 1)
                if result_dict[keyword]["total bottom ads"] != 0:
                    bottom_percentage = round(
                        result_dict[keyword][company]["bottom"] / result_dict[keyword]["total bottom ads"] * 100, 1)

                result_list.append(
                    [
                        keyword,
                        company,
                        result_dict[keyword][company]["absolute-top"],
                        result_dict[keyword][company]["top"],
                        result_dict[keyword][company]["bottom"],
                        top_percentage,
                        bottom_percentage,
                        round((result_dict[keyword]["total top ads"] + result_dict[keyword]
                               ["total bottom ads"]) / (number_of_times * 2) * 100, 1),
                    ]
                )
        else:
            result_list.append([keyword, None, 0, 0, 0, 0, 0, 0])

    df = pd.DataFrame(result_list, columns=["Keyword", "Company", "absolute-top",
                                            "top", "bottom", "top(%)", "bottom(%)", "Keyword Ads Percentage(%)"])
    return df


# Dashboard configuration title
st.title(":male-detective: Google Ads Keyword Dashboard")

# Specify the number of times each keyword should be scraping running
# 1 = lower bound , 100 = high bound, 10 = initial bound
number_of_times = st.slider(
    'How many times do you want this keyword scraping to be run?', 1, 100, 10)

# List of keywords that should be scraped
list_of_keywords = ["UnoFinans", "Okida", "ZenFinans",
                    "My Bank ASA", "Odontia", "Vende Finans AS", "Mileni", "Finepart",
                    "MER Finans", "Balder AB", "Digtective", "Google", "Nyhetebrev", "Lånekalkulator.no", "Norsk Refinansiering",
                    "Capital Box Finland", "Ai Finans", "Direct"]

# Define columns for each keyword
col1, col2 = st.columns(2)
with col1:
    chosen_keywords = st_tags(
        label='Add Keywords here!',
        text='Press enter to add more',
        value=list_of_keywords,
        suggestions=["Google", "ZenFinans", "Privatmegleren", "GoodCash"],
        maxtags=100,
        key="aljnf"
    )

with col2:
    st.caption('Current List of Keywords')
    st.write((chosen_keywords))

submitted = st.button("Submit")

if submitted:
    st.write('Google Ads Scraping for the following keywords:',
             str(chosen_keywords), ' for ', number_of_times, ' times.')

    result_dict = ad_scraper(number_of_times, chosen_keywords)
    raw_output = json_to_data_frame(result_dict, chosen_keywords)
    raw_output.to_csv('./src/ad_scrape_result.csv', index=False)


display_result = st.button("Display Result")
if display_result:
    display_scraper_result()
