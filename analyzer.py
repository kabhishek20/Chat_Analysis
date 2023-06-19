import re
import functions
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Chat Analysis",
    page_icon="logo.png",
    layout="wide"
)

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

def preprocess(data):
    pattern = '\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)
    df = pd.DataFrame({'user_message': messages, 'message_date': dates})

    df['message_date'] = pd.to_datetime(df['message_date'], format='%m/%d/%y, %H:%M - ')
    df.rename(columns={'message_date': 'date'}, inplace=True)

    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split('([\w\W]+?):\s', message)
        if entry[1:]:  # user name
            users.append(entry[1])
            messages.append(" ".join(entry[2:]))
        else:
            users.append('group_notification')
            messages.append(entry[0])

    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message'], inplace=True)  

    df['date'] = pd.to_datetime(df['date'],format='%m/%d/%y, %H:%M - ')
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    period = []
    for hour in df[['day_name', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour + 1))
        else:
            period.append(str(hour) + "-" + str(hour + 1))

    df['period'] = period
    return(df)

if __name__=='__main__':
    st.sidebar.title(":red[WhatsApp Analyzer]")
    st.sidebar.caption("This is an application where you can analyze your WhatsApp chats. Please take care that the chats uploaded are in 24 hour format.")
    uploaded_file = st.sidebar.file_uploader("Upload your Chats")
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        data = bytes_data.decode("utf-8")
        df = preprocess(data)
        # st.dataframe(df)

        user_list = df['user'].unique().tolist()
        user_list.remove('group_notification')
        user_list.sort()
        user_list.insert(0,"Overall")
        selected_user = st.sidebar.selectbox("Select Username",user_list)

        if st.sidebar.button("Analyze"):
            num_messages, words, num_media_messages, num_links = functions.fetch_stats(selected_user,df)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("#### :blue[Total Messages]")
                st.markdown("#### "+str(num_messages))
            with col2:
                st.markdown("#### :blue[Total Words]")
                st.markdown("#### "+str(words))
            with col3:
                st.markdown("#### :blue[Media Shared]")
                st.markdown("#### "+str(num_media_messages))
            with col4:
                st.markdown("#### :blue[Links Shared]")
                st.markdown("#### "+str(num_links))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### :blue[Monthly Timeline]")
                timeline = functions.monthly_timeline(selected_user,df)
                fig,ax = plt.subplots()
                ax.plot(timeline['time'], timeline['message'],color='purple')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col2:
                st.markdown("#### :blue[Daily Timeline]")
                daily_timeline = functions.daily_timeline(selected_user, df)
                fig, ax = plt.subplots()
                ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='orange')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)  

            col1,col2 = st.columns(2)

            with col1:
                st.markdown("#### :blue[Most busy day]")
                busy_day = functions.week_activity_map(selected_user,df)
                fig,ax = plt.subplots()
                ax.bar(busy_day.index,busy_day.values,color='purple')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)

            with col2:
                st.markdown("#### :blue[Most busy month]")
                busy_month = functions.month_activity_map(selected_user, df)
                fig, ax = plt.subplots()
                ax.bar(busy_month.index, busy_month.values,color='orange')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)

            st.markdown("#### :blue[Weekly Activity Map]")
            user_heatmap = functions.activity_heatmap(selected_user,df)
            fig,ax = plt.subplots()
            ax = sns.heatmap(user_heatmap)
            st.pyplot(fig)

            if selected_user == "Overall":
                st.markdown("#### :blue[Most Busy Users]")
                x,new_df = functions.most_busy_users(df)
                fig, ax = plt.subplots()

                col1, col2 = st.columns(2)
                with col1:
                    ax.bar(x.index,x.values,color="orange")
                    plt.xticks(rotation="vertical")
                    st.pyplot(fig) 
                with col2:
                    st.dataframe(new_df)     

            st.markdown("#### :blue[WordCloud]")
            df_wc = functions.create_wordcloud(selected_user,df)
            fig,ax = plt.subplots()
            ax.imshow(df_wc)
            st.pyplot(fig)    

            st.markdown("#### :blue[Frequently used Words]")
            most_common_df = functions.most_common_words(selected_user,df)
            fig,ax = plt.subplots()
            ax.barh(most_common_df[0],most_common_df[1],color="orange")
            plt.xticks(rotation="vertical")
            st.pyplot(fig)

            st.markdown("#### :blue[Emoticons Analysis]")
            emoji_df = functions.emoji_helper(selected_user,df)
            col1,col2 = st.columns(2)
            with col1:
                st.dataframe(emoji_df)
            with col2:
                fig,ax = plt.subplots()
                ax.pie(emoji_df[1].head(),labels=emoji_df[0].head(),autopct="%0.2f")
                st.pyplot(fig)
            
