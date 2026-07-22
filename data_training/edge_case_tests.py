from validation import validate_input

tests = [

    {
        "gpa":5.2,
        "skills_count":5,
        "prior_projects":2,
        "track":"AI"
    },

    {
        "gpa":3.5,
        "skills_count":3,
        "prior_projects":1,
        "track":"Cyber Security"
    },

    {
        "gpa":2.8,
        "skills_count":-1,
        "prior_projects":1,
        "track":"Data"
    },

    {
        "skills_count":5,
        "prior_projects":2,
        "track":"Web"
    }

]

for test in tests:

    print(validate_input(test))
