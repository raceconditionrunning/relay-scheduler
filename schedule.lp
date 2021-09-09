#program base.

% Time, Station, Station

% From Angle Lake to Northgate
leg(T - 18, 18 - (T - 18), 18 - (T - 17)) :- T=18..35.

%leg(T, T, T + 1) :- T=0..17.
%leg(T, 18 - (T - 18), 18 - (T - 17)) :- T=18..35.

error("Leg station isn't a station", S1) :- leg(_, S1, _), not station(S1).
error("Leg station isn't a station", S2) :- leg(_, _, S2), not station(S2).
error("Leg not continous", S1, S2) :- leg(_, S1, S2), |S1 - S2| != 1.
error("Leg not continous", T) :- leg(T, S1, S2), leg(T + 1, S3, S4), S2 != S3.
%#show leg/3.


%%% Generate

% One person each leg
%1{
%    run_leg(X,leg(A,B,C)): participant(X)
%}1 :- leg(A,B,C).

% Multiple people (potentially) each leg

1{
   run_leg(X, leg(A,B,C)): participant(X) 
}7 :- leg(A,B,C).
%#show run_leg/2.

% Who runs what index
run(X,T) :- run_leg(X, leg(T,_,_)).
%#show run/2.

% Summarize assignments
assignment(N,SN0,SN3) :- s_name(S0, SN0), s_name(S3, SN3), leg(T1, S2, S3), leg(T0, S0, S1), T1=#max{T:run(X, T), T=0..18}, T0=#min{T:run(X,T), T=0..18}, name(X, N), participant(X).
#show assignment/3.

%%% Plan events

exchange(X, T) :- run(X, T), not run(X, T - 1), participant(X), T=0..17.
exchange(X, T) :- not run(X, T), run(X, T - 1), participant(X), T=0..18.
%#show exchange/2.

%%% Plan metrics

leg_pace(T, M) :- M = #max{P:run(X, T), preferred_pace(X,P), participant(X)}, T=0..17. 
#show leg_pace/2.

%duration(T, Duration) :- Duration = Distance * M, leg_dist(T,Distance), leg_pace(T, M), T=0..17.

%total_duration(S) :- S = #sum{Duration: duration(0..17, Duration)}.
%#show total_duration/1.
#show duration/2.

leg_count(X, C) :- C = #count{run(X, T): run(X, T), participant(X)}, participant(X).
#show leg_count/2.
:- leg_count(X, 0), participant(X).

leg_dist(T, D) :- leg(T, S1, S2), distance(S1, S2, D).
%#show leg_dist/2.

total_dist(X, T) :- T = #sum{D: distance(S1, S2, D), run_leg(X,leg(_,S1,S2)), participant(X)}, participant(X).
#show total_dist/2.

deviation(X, |G - T|) :- total_dist(X, T), preferred_distance(X, G), participant(X).
%#show deviation/2.

leg_coverage(T, C) :- C = #count{run(X, T): run(X, T), participant(X)}, T=0..18.
%#show leg_coverage/2.

exchange_count(X, C) :- C = #count{exchange(X,T): exchange(X,T), participant(X), T=0..18}, participant(X).
%#show exchange_count/2.


%%% Objectives

% Make people run the distance they want to run
#minimize {D: deviation(X, D), participant(X)}.

:- C > 2, exchange_count(X, C), participant(X).


#show error/2.
#show error/3.