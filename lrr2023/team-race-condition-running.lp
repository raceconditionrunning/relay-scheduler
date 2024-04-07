% Lexicographic optimization. Objectives from most to least important. Reorder or remove objectives here
objective(
    4,"dist-pref-overage";
    3,"dist-pref";
    2,"commute-pref";
    1,"duration";
    0,"leader-early-start";
    -1,"leaders-ignored";
    -2,"pace-pref"
).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Preferences
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

preference(
    "Chandra Nandi", 7, "12.0", "10:00", 1;
    "James Wilcox", 14, "6.0", "10:30", 1;
    "Jingwei Ma", 17, "6.0", "11:00", 0;
    "Margaret Li", -1, "10.0", "10:00", 0;
    "Kevin Mu", 16, "5.0", "10:00", 0;
    "Dhruba Ghosh", 14, "7.0", "9:00", 0;
    "Lauren Bricker", 17, "6.0", "12:30", 0;
    "Stephen Spencer", 17, "6.0", "10:30", 0;
    "Yuxuan Mei", 17, "5.0", "13:00", 1;
    "Divyansh Pareek", 14, "2.0", "7:30", 0;
    "Zachary Tatlock", 6, "6.0", "10:30", 1;
    "Nisha Devasia", 15, "5.0", "9:00", 0;
    "Dale Berg", 15, "20.0", "9:00", 0;
    "Edward Misback", 16, "4.0", "9:00", 1;
    "Josh Horowitz", -1, "15.0", "10:00", 0;
    "Ethan Weinberger", 14, "15.0", "9:00", 1;
    "Varad Dhat", -1, "5.0", "12:04", 0;
    "Hannah Lee", -1, "11.0", "09:45", 0;
    "Theo Gregersen", -1, "15.0", "9:30", 0;
    "Nick Walker", 16, "20.0", "10:00", 1;
    "Patrick Yu", 16, "1.0", "10:00", 0;
    "Anshul Nasery", 16, "1.0", "10:00", 0
).

% Needs to start
:- not exchangeVisit("Nick Walker", 0).

% Wants to start
:- not exchangeVisit("Josh Horowitz", 0).

% Schedule together (unused; solutions already satisfied)
%:- run("Stephen Spencer", X), not run("Lauren Bricker", X).
%:- not run("Stephen Spencer", X), run("Lauren Bricker", X).