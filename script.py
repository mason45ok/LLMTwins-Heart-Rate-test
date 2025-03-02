from HeartRateSetting import setup_google_sheet, update_blood_oxygen_value, update_heart_rate_value, time_label
def main():
    worksheet = setup_google_sheet()
    update_blood_oxygen_value(worksheet)
    update_heart_rate_value(worksheet)
    time_label(worksheet)
    print(f"執行成功:{update_heart_rate_value(worksheet)},{update_blood_oxygen_value(worksheet)},{time_label(worksheet)}")
if __name__ == "__main__":
    main()