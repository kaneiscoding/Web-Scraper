import getpass
from numpy import NaN
from pandas.core.series import Series
from selenium import webdriver
import time
import requests
import lxml.html as lh
import pandas as pd
import bs4 as bs
from functools import reduce

# create dataframe with all HW and quiz href and student starting points (these may need to be changed if edits are made to the assessment tool)
meta_data = {'Quiz1':[361, 91795], 'Quiz2':[300, 76084], 'Quiz3':[305, 77753], 'Final':[307, 78573]}
meta_df = pd.DataFrame.from_dict(meta_data, orient='index', columns=['assessment_href', 'student_start_number'])

# def LOG IN
# enter username, password and desired assessment
#my_user = getpass.getpass("Username:\n")
my_user = "kane1"
#my_pass = getpass.getpass("Password:\n")
my_pass = "Cheech911tracks"
#assessment = getpass.getpass("Assessment (ex: HW5):\n")
assessment = "Quiz1"
#define number of students in the class
num_students = 420
print(my_user)
print(my_pass)
print(assessment)

# open chrome, go to specified website 
browser = webdriver.Chrome()
url = "https://apps.srv.ualberta.ca/bus/oa"
browser.get(url)

time.sleep(1)

#find login button and click it 
login_string = "//a[contains(@href, '/Login')]"
login_link = browser.find_element_by_xpath(login_string)
login_href = login_link.get_attribute("href")
browser.get(login_href)

#enter username
username_el = browser.find_element_by_name("username")
username_el.send_keys(my_user)

#enter password
password_el = browser.find_element_by_name("password")
password_el.send_keys(my_pass)

#click submit
time.sleep(0.5)
submit_btn_el= browser.find_element_by_css_selector("input[type='submit']")
submit_btn_el.click()

#find course link and click it 
time.sleep(0.5)
course_string = "//a[contains(@href, '/Course/Details/30')]"
course_link = browser.find_element_by_xpath(course_string)
course_href = course_link.get_attribute("href")
browser.get(course_href)

#find assessment link and click it (have to enter specific href)
time.sleep(0.5)
assessment_number = meta_df.loc[[assessment], ['assessment_href']]
assessment_number = str(assessment_number.iloc[0,0])
assessment_string = "//*[contains(@href, '/bus/oa/Assessments/Details/"+ assessment_number +"')]"
assessment_link = browser.find_element_by_xpath(assessment_string)
assessment_href = assessment_link.get_attribute("href")
browser.get(assessment_href)

#click Student Views button
time.sleep(0.5)
student_views_string = "//*[contains(@href, '/bus/oa/Assessments/Students/"+ assessment_number +"')]"
student_views_link = browser.find_element_by_xpath(student_views_string)
student_views_href = student_views_link.get_attribute("href")
browser.get(student_views_href)

# parse through the table 
df = pd.read_html(browser.find_element_by_css_selector('table').get_attribute('outerHTML'))[0]
df[['Last Name', 'First Name']] = df['Name'].str.split(',', expand=True)
#df.drop('Detailed Marks', axis=1, inplace=True)
cols = df.columns.tolist()
cols = ['Name', 'CCID', 'Last Name', 'First Name', 'Group']
df = df[cols]

# create loop to go into student assessmnet and extract download time 
i = meta_df.loc[[assessment], ['student_start_number']]
i = i.iloc[0,0]
x = 0
dl_times = []
dl_student_names = []
submission_data = {'Attempt':[], 'Submission Date':[], 'Original Name':[]}
submission_times = pd.DataFrame.from_dict(submission_data)
temp_table_initial = {'Name':[], 'Attempt':[], 'Submission Date':[], 'Original Name':[]}
temp_table = pd.DataFrame.from_dict(temp_table_initial)

while x <=num_students:
    time.sleep(0.1)
    try:
        browser.get("https://apps.srv.ualberta.ca/bus/oa/Assessments/StudentAssessment/"+str(i))
    except:
        pass
    i += 1
    # scrape the submissions table
    try:
        temp_table = pd.read_html(browser.find_element_by_css_selector('table').get_attribute('outerHTML'))[0]
    except:
        pass
    # only takes the most recent submission data
    try:
        temp_table = temp_table.loc[temp_table['Attempt']==max(temp_table['Attempt'])]
        name_string= "//*[contains(text(), '(Assessment)')]"
        name_el = browser.find_element_by_xpath(name_string)
        student_name = name_el.get_attribute("innerHTML")
        print(student_name)
        temp_table.loc[temp_table.index[0], 'Name'] = student_name
        print(temp_table)

    except:
        temp_table_data ={'Attempt':[NaN], 'Submission Date':[NaN], 'Original Name':[NaN]}
        temp_table = pd.DataFrame.from_dict(temp_table_data)
        try:
            name_string= "//*[contains(text(), '(Assessment)')]"
            name_el = browser.find_element_by_xpath(name_string)
            student_name = download_data_el.get_attribute("innerHTML")
            temp_table.loc[temp_table.index[0], 'Name'] = student_name
        except:
            temp_table.loc[temp_table.index[0], ['Name', 'Attempt', 'Submission Date', 'Original Name']] = 'NA'

    # store the data in the permanent submission data table 
    submission_times = submission_times.append(temp_table)
    
    # scrape the download time 
    try:
        download_data_string = "//*[contains(text(), 'assessment file')]"
        download_data_el = browser.find_element_by_xpath(download_data_string)
        download_data = download_data_el.get_attribute("innerHTML")
        dl_times += [download_data]

        name_string= "//*[contains(text(), '(Assessment)')]"
        name_el = browser.find_element_by_xpath(name_string)
        student_name = name_el.get_attribute("innerHTML")
        dl_student_names += [student_name]
    except:
        pass
    x += 1
    print(x)

#convert dl_times to dataframe, add dl_times to the main dataframe: submission times
dl_times_df = pd.DataFrame({'Name':dl_student_names, 'download_times':dl_times})


dl_times_df['Name'] = dl_times_df['Name'].map(lambda x: x.rstrip('(Assessmnet)'))
submission_times['Name'] = submission_times['Name'].map(lambda x: x.rstrip('(Assessmnet)'))
submission_times = submission_times[submission_times.notna()]
#merge data frames with unique key = full names 

df.reset_index(drop = True, inplace=True)
dl_times_df.reset_index(drop = True, inplace=True)
submission_times.reset_index(drop = True, inplace=True)
index = pd.Series(range(0,394))
dfs = [df, dl_times_df, submission_times]
print(df)
print(dl_times_df)
print(submission_times)
#submission_and_data_df = pd.merge(submission_times, dl_times_df, how='left', on='Name')
#joined_df = pd.merge(df, submission_and_data_df, how='left', on='Name')
df_final = pd.concat(dfs, axis=1, join='inner')
#drop full names after merged 
df_final.to_csv('student_submissions.csv', index=False)
