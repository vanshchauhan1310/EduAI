def get_recommendation(level):

    mapping = {
        "Low":
        "Continue regular monitoring",

        "Medium":
        "Schedule counselling and monitor attendance",

        "High":
        "Immediate intervention required. Contact guardian and create retention plan"
    }

    return mapping[level]