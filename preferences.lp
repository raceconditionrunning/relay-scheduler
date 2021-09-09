name(
    0, "Yuxuan";
    1, "James";
    2, "Jennifer";
    3, "Chandra";
    4, "Ellis";
    5, "Nick";
    6, "Zach";
    7, "Max";
    8, "Swati";

).

participant(X) :- name(X, _).

% Person, Station
nearest_station(
    0, 3;
    1, 4;
    2, 16;
    3, 0;
    4, 4;
    5, 2;
    6, 13;
    7, 5;
    8, 2;
    ).

preferred_distance(
    0, "5.0";
    1, "6.0";
    2, "3.0";
    3, "10.0";
    4, "20.0";
    5, "8.0";
    6, "6.0";
    7, "3.0";
    8, "6.2"
    ).

preferred_pace(
    0, "11.33";
    1, "9.0";
    2, "10.0";
    3, "10.0";
    4, "7.5";
    5, "9.0";
    6, "10.5";
    7, "9.5";
    8, "12.0";
).