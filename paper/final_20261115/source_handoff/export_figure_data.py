import csv
from pathlib import Path
p=Path(__file__).parent/'figure_data';p.mkdir(exist_ok=True)
def dump(name,fields,rows):
 with (p/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(fields);w.writerows(rows)
dump('topology_edges_derived_from_d7_summary.csv',['src','dst','beta'],[[1,3,.08],[1,4,.09],[2,3,.10],[4,3,.11],[4,5,.07],[4,6,.12],[3,5,.10],[6,5,.05]])
dump('resource_means_from_d7_summary.csv',['asset','B06','B12','B18'],[['v1_API',.339102,.463738,.480837],['v2_Web',.116986,.225360,.249486],['v3_Order',.056986,.140469,.162958],['v4_Identity',.012188,.076786,.101903],['v5_Database',.037143,.062960,.073916],['v6_Admin',.001960,.005190,.011925]])
vals=[(.6,'a0',9.760493,9.759868),(.6,'aG',9.620103,9.620736),(.6,'aBRF',9.620834,9.621622),(1.2,'a0',9.467228,9.466796),(1.2,'aG',9.326647,9.327081),(1.2,'aBRF',9.326860,9.327376),(1.8,'a0',9.449465,9.449058),(1.8,'aG',9.310823,9.311232),(1.8,'aBRF',9.310880,9.311360)]
dump('cross_evaluation_summary_restructured.csv',['B','common_attack','JD_G','JD_F','G_minus_F_rounded'],[(B,a,G,F,round(G-F,6)) for B,a,G,F in vals])
roll=[(.6,'E0',7.450623,7.447613,7.447232,.040393,.045501),(.6,'E1',7.431210,7.422472,7.423012,.117591,.110316),(1.2,'E0',6.925324,6.921314,6.920807,.057912,.065226),(1.2,'E1',6.901625,6.890208,6.890813,.165432,.156664),(1.8,'E0',6.825423,6.821366,6.820818,.059432,.067461),(1.8,'E1',6.801935,6.790200,6.790840,.172527,.163117)]
dump('event_post_loss_summary_restructured.csv',['B','execution_attack','J_P','J_G','J_R','improve_G_vs_P_pct_from_D7','improve_R_vs_P_pct_from_D7'],roll)
print('saved 4 figure data csvs; source: accessible D8-1 text, not original CSV')
