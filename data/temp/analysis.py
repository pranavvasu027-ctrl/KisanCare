import pandas as pd
import numpy as np
import os

# ── Setup ──
df = pd.read_csv("social_media_students.csv")
os.makedirs("exports", exist_ok=True)
print("✅ Dataset loaded:", len(df), "students")

# ══════════════════════════════════════════
# 1. MAIN DATA
# ══════════════════════════════════════════
df.to_csv("exports/01_main_data.csv", index=False)
print("✅ 01_main_data.csv")

# ══════════════════════════════════════════
# 2. KPI SUMMARY (Pearson r calculated manually)
# ══════════════════════════════════════════
x = df['Daily_Usage_Hours']
y = df['CGPA']
r = ((x - x.mean()) * (y - y.mean())).sum() / (
    ((x - x.mean())**2).sum() * ((y - y.mean())**2).sum()) ** 0.5
r = round(r, 2)

kpi = pd.DataFrame([{
    'Total_Students'          : len(df),
    'Avg_Daily_Usage_Hrs'     : round(df['Daily_Usage_Hours'].mean(), 2),
    'Avg_CGPA'                : round(df['CGPA'].mean(), 2),
    'Avg_Addiction_Score'     : round(df['Addiction_Score'].mean(), 2),
    'Avg_Sleep_Hours'         : round(df['Sleep_Hours'].mean(), 2),
    'Avg_Mental_Health_Score' : round(df['Mental_Health_Score'].mean(), 2),
    'Avg_Conflicts_Per_Month' : round(df['Conflicts_Per_Month'].mean(), 2),
    'Pct_Affected_Academic'   : round((df['Affects_Academic_Performance']=='Yes').mean()*100, 1),
    'Pct_High_Addiction'      : round((df['Addiction_Score'] >= 6).mean()*100, 1),
    'Pearson_r'               : r,
}])
kpi.to_csv("exports/02_kpi_summary.csv", index=False)
print("✅ 02_kpi_summary.csv  |  Pearson r =", r)

# ══════════════════════════════════════════
# 3. CGPA BY USAGE TIER
# ══════════════════════════════════════════
tier_order = ['<2 hrs','2-4 hrs','4-6 hrs','6+ hrs']
tier = df.groupby('Usage_Tier').agg(
    Avg_CGPA          =('CGPA','mean'),
    Avg_Sleep         =('Sleep_Hours','mean'),
    Avg_Addiction     =('Addiction_Score','mean'),
    Avg_Mental_Health =('Mental_Health_Score','mean'),
    Avg_Conflicts     =('Conflicts_Per_Month','mean'),
    Student_Count     =('Student_ID','count')
).round(2).reset_index()
tier['Usage_Tier'] = pd.Categorical(tier['Usage_Tier'], categories=tier_order, ordered=True)
tier = tier.sort_values('Usage_Tier')
tier.to_csv("exports/03_cgpa_by_usage_tier.csv", index=False)
print("✅ 03_cgpa_by_usage_tier.csv")

# ══════════════════════════════════════════
# 4. PLATFORM ANALYSIS
# ══════════════════════════════════════════
platform = df.groupby('Most_Used_Platform').agg(
    Avg_CGPA      =('CGPA','mean'),
    Avg_Usage_Hrs =('Daily_Usage_Hours','mean'),
    Avg_Addiction =('Addiction_Score','mean'),
    Avg_Sleep     =('Sleep_Hours','mean'),
    Student_Count =('Student_ID','count')
).round(2).reset_index().sort_values('Avg_CGPA')
platform.to_csv("exports/04_platform_analysis.csv", index=False)
print("✅ 04_platform_analysis.csv")

# ══════════════════════════════════════════
# 5. COUNTRY ANALYSIS
# ══════════════════════════════════════════
country = df.groupby('Country').agg(
    Avg_Addiction =('Addiction_Score','mean'),
    Avg_CGPA      =('CGPA','mean'),
    Avg_Usage     =('Daily_Usage_Hours','mean'),
    Student_Count =('Student_ID','count')
).round(2).reset_index().sort_values('Avg_Addiction', ascending=False)
country.to_csv("exports/05_country_analysis.csv", index=False)
print("✅ 05_country_analysis.csv")

# ══════════════════════════════════════════
# 6. SLEEP VS USAGE
# ══════════════════════════════════════════
df[['Student_ID','Daily_Usage_Hours','Sleep_Hours','Usage_Tier','CGPA','Addiction_Score']]\
    .to_csv("exports/06_sleep_vs_usage.csv", index=False)
print("✅ 06_sleep_vs_usage.csv")

# ══════════════════════════════════════════
# 7. MENTAL HEALTH VS ADDICTION
# ══════════════════════════════════════════
df[['Student_ID','Addiction_Score','Mental_Health_Score','Conflicts_Per_Month','Usage_Tier']]\
    .to_csv("exports/07_mental_health.csv", index=False)
print("✅ 07_mental_health.csv")

# ══════════════════════════════════════════
# 8. RELATIONSHIP STATUS ANALYSIS
# ══════════════════════════════════════════
df.groupby('Relationship_Status').agg(
    Avg_Addiction =('Addiction_Score','mean'),
    Avg_CGPA      =('CGPA','mean'),
    Avg_Usage     =('Daily_Usage_Hours','mean'),
    Avg_Sleep     =('Sleep_Hours','mean'),
    Student_Count =('Student_ID','count')
).round(2).reset_index().to_csv("exports/08_relationship_analysis.csv", index=False)
print("✅ 08_relationship_analysis.csv")

# ══════════════════════════════════════════
# 9. GENDER ANALYSIS
# ══════════════════════════════════════════
df.groupby('Gender').agg(
    Avg_CGPA      =('CGPA','mean'),
    Avg_Usage     =('Daily_Usage_Hours','mean'),
    Avg_Addiction =('Addiction_Score','mean'),
    Student_Count =('Student_ID','count')
).round(2).reset_index().to_csv("exports/09_gender_analysis.csv", index=False)
print("✅ 09_gender_analysis.csv")

# ══════════════════════════════════════════
# 10. ACADEMIC LEVEL ANALYSIS
# ══════════════════════════════════════════
df.groupby('Academic_Level').agg(
    Avg_CGPA      =('CGPA','mean'),
    Avg_Usage     =('Daily_Usage_Hours','mean'),
    Avg_Addiction =('Addiction_Score','mean'),
    Avg_Sleep     =('Sleep_Hours','mean'),
    Student_Count =('Student_ID','count')
).round(2).reset_index().to_csv("exports/10_academic_level.csv", index=False)
print("✅ 10_academic_level.csv")

# ══════════════════════════════════════════
# 11. ADDICTION SCORE DISTRIBUTION
# ══════════════════════════════════════════
bins   = [0, 2, 4, 6, 8, 10]
labels = ['1-2','3-4','5-6','7-8','9-10']
df['Addiction_Bin'] = pd.cut(df['Addiction_Score'], bins=bins, labels=labels)
addict_dist = df['Addiction_Bin'].value_counts().reset_index()
addict_dist.columns = ['Addiction_Range','Student_Count']
addict_dist.sort_values('Addiction_Range').to_csv("exports/11_addiction_distribution.csv", index=False)
print("✅ 11_addiction_distribution.csv")

# ══════════════════════════════════════════
# 12. AFFECTED vs NOT AFFECTED
# ══════════════════════════════════════════
df.groupby('Affects_Academic_Performance').agg(
    Avg_CGPA  =('CGPA','mean'),
    Avg_Usage =('Daily_Usage_Hours','mean'),
    Avg_Sleep =('Sleep_Hours','mean'),
    Count     =('Student_ID','count')
).round(2).reset_index().to_csv("exports/12_affected_vs_not.csv", index=False)
print("✅ 12_affected_vs_not.csv")

print("\n🎉 All 12 files saved in exports/ folder!")
print("📂 Now open Power BI and load from the exports folder.")

# ══════════════════════════════════════════
# 13. AGE ANALYSIS
# ══════════════════════════════════════════
age = df.groupby('Age').agg(
    Avg_CGPA          =('CGPA','mean'),
    Avg_Usage         =('Daily_Usage_Hours','mean'),
    Avg_Addiction     =('Addiction_Score','mean'),
    Avg_Sleep         =('Sleep_Hours','mean'),
    Avg_Mental_Health =('Mental_Health_Score','mean'),
    Student_Count     =('Student_ID','count')
).round(2).reset_index().sort_values('Age')
age.to_csv("exports/13_age_analysis.csv", index=False)
print("✅ 13_age_analysis.csv")

print("\n🎉 All 13 files saved in exports/ folder!")
print("📂 Now open Power BI and refresh!")
