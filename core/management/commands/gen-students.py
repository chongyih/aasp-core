import random

# parameters
NUM_GROUPS = 15
STUDENTS_PER_GROUP = 40

# name sets
first_name_partial = {"Wei", "Jun", "Ting", "Chun", "Hong", "Kai", "Min", "Mei", "Ming", "Meng", "Yan", "Zheng", "Song", "Kian", "Yuan", "Guo", "Yin",
                      "Ren"}
first_name_complete = {"Ryan", "Joshua", "Sean", "Adam", "Jonathan", "Damien", "Nicholas", "Darren", "Alex", "Jason", "Eugene", "Adriel", "Martin",
                       "Michelle", "Sarah", "Joy", "Joyce", "Rachel", "Nicole", "Yi Ling", "Ashley", "Felicia", "Cherilyn"}
last_names = {"Tan", "Chan", "Chong", "Chen", "Sim", "Wang", "Li", "Lim", "Tang", "Lin", "Lau", "Zhang", "Cheng", "Liu", "Lai", "Quek", "Ng", "Huang",
              "Seah", "Pang", "Yang", "Neo", "Han", "Gan"}

# generate possible first_names
first_names = set()
for i in first_name_partial:
    for j in first_name_partial:
        first_names.add(f"{i} {j}")
first_names.update(first_name_complete)


# generate actual data
with open("students.csv", "w") as f:
    usernames = set()
    for cg in range(1, NUM_GROUPS+1):
        course_group = f"CS{cg}"
        for s in range(STUDENTS_PER_GROUP):
            first_name = random.choice(list(first_names))
            last_name = random.choice(list(last_names))
            while True:
                username = f"{first_name[:2]}{last_name[:2]}{random.randint(100,999)}".upper()
                if username not in usernames:
                    usernames.add(username)
                    break
                else:
                    continue

            f.write(f"{first_name},{last_name},{username},{course_group}\n")

