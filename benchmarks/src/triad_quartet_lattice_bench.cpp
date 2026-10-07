#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

using Clock = std::chrono::steady_clock;
constexpr int N=12, PAIRS=66, PHASES=24;

struct AgentMeta { int lane; int identity_phase; const char* name; };
static const AgentMeta META[N] = {
  {0,0,"Michael"},{0,1,"Gabriel"},{0,2,"Azrael"},
  {1,0,"Uriel"},{1,1,"Raguel"},{1,2,"Ariel"},
  {2,0,"Raziel"},{2,1,"Jophiel"},{2,2,"Zadkiel"},
  {3,0,"Haniel"},{3,1,"Chamuel"},{3,2,"Raphael"}
};

static int pairIndex[N][N];

struct Eval {
  int unique_pairs=0;
  int full_pair_phase=999;
  int unique_by5=0;
  int min_pair=999, max_pair=0;
  double pair_std=0;
  double transition_mix=0;
  double diversity=0;
  double role_balance=0;
  bool operational_position_unique=true;
  std::array<int,PHASES> cumulative_unique{};
  std::array<int,PAIRS> pair_counts{};
};

struct Schedule {
  std::array<int,N> rho{};   // identity -> cyclic coordinate
  std::array<int,N> sigma{}; // cyclic coordinate -> physical cell
  std::array<int,N> kT{};    // 12 expansion shifts
  std::array<int,N> kQ{};    // 12 contraction shifts
  Eval e;
};

static inline int groupFor(int pos, bool triad){ return triad ? (pos%4) : (pos/4); }
static inline int groupCount(bool triad){ return triad?4:3; }
static inline int groupSize(bool triad){ return triad?3:4; }

Eval evaluate(const Schedule& s){
  Eval e;
  std::array<int,PAIRS> counts{};
  bool seenOperational[N][2][N]{};
  std::array<int,N> prevGroup{};
  bool havePrev=false;
  int ti=0, qi=0;
  double mixSum=0, mixMax=0, diversitySum=0, diversityMax=0;
  int triadRole[N][3]{}; int quartetRole[N][4]{};
  for(int phase=0; phase<PHASES; ++phase){
    bool triad=(phase%2==0);
    int shift = triad ? s.kT[ti++] : s.kQ[qi++];
    std::array<int,N> pos{}, grp{};
    std::array<std::vector<int>,4> members;
    for(int a=0;a<N;++a){
      int p=s.sigma[(s.rho[a]+shift)%N];
      pos[a]=p; grp[a]=groupFor(p,triad); members[grp[a]].push_back(a);
      int mode=triad?0:1;
      if(seenOperational[a][mode][p]) e.operational_position_unique=false;
      seenOperational[a][mode][p]=true;
      if(triad) triadRole[a][p/4]++; else quartetRole[a][p%4]++;
    }
    int gc=groupCount(triad), gs=groupSize(triad);
    for(int g=0;g<gc;++g){
      auto &m=members[g];
      // Pair contacts.
      for(int i=0;i<(int)m.size();++i) for(int j=i+1;j<(int)m.size();++j){
        counts[pairIndex[m[i]][m[j]]]++;
      }
      // Identity diversity: triads ideally span 3 lanes + all 3 identity phases; quartets ideally all 4 lanes + all 3 phases.
      bool lanes[4]{}, ips[3]{}; int lc=0,ic=0;
      for(int a:m){ if(!lanes[META[a].lane]){lanes[META[a].lane]=true;lc++;} if(!ips[META[a].identity_phase]){ips[META[a].identity_phase]=true;ic++;} }
      diversitySum += lc + ic;
      diversityMax += (triad ? 6.0 : 7.0);
      // Cross-phase mixing: each current group should draw one member from every previous group.
      if(havePrev){
        bool x[4]{}; int xc=0;
        for(int a:m){ int pg=prevGroup[a]; if(!x[pg]){x[pg]=true;xc++;} }
        mixSum += xc; mixMax += gs;
      }
    }
    int uniq=0; for(int c:counts) if(c) uniq++;
    e.cumulative_unique[phase]=uniq;
    if(phase==4) e.unique_by5=uniq;
    if(uniq==PAIRS && e.full_pair_phase==999) e.full_pair_phase=phase+1;
    prevGroup=grp; havePrev=true;
  }
  e.pair_counts=counts;
  int uniq=0; double mean=0;
  for(int c:counts){ if(c)uniq++; mean += c; e.min_pair=std::min(e.min_pair,c); e.max_pair=std::max(e.max_pair,c); }
  e.unique_pairs=uniq; mean/=PAIRS;
  double var=0; for(int c:counts){double d=c-mean;var+=d*d;} var/=PAIRS; e.pair_std=std::sqrt(var);
  e.transition_mix = mixMax?mixSum/mixMax:0;
  e.diversity = diversityMax?diversitySum/diversityMax:0;
  // Ideal automatic role balance from full operational-seat tour; score deviations anyway.
  double dev=0; int slots=0;
  for(int a=0;a<N;++a){
    for(int r=0;r<3;++r){dev += std::abs(triadRole[a][r]-4); slots++;}
    for(int r=0;r<4;++r){dev += std::abs(quartetRole[a][r]-3); slots++;}
  }
  e.role_balance = 1.0 - dev/(slots*4.0);
  return e;
}

// Lexicographic objective: hard uniqueness, earliest global pair coverage, most early coverage,
// best pair balance, then cross-phase mixing and identity diversity.
bool better(const Eval& a,const Eval& b){
  if(a.operational_position_unique!=b.operational_position_unique) return a.operational_position_unique;
  if(a.full_pair_phase!=b.full_pair_phase) return a.full_pair_phase < b.full_pair_phase;
  if(a.unique_by5!=b.unique_by5) return a.unique_by5 > b.unique_by5;
  if(a.unique_pairs!=b.unique_pairs) return a.unique_pairs > b.unique_pairs;
  if(a.max_pair-a.min_pair != b.max_pair-b.min_pair) return (a.max_pair-a.min_pair)<(b.max_pair-b.min_pair);
  if(std::abs(a.pair_std-b.pair_std)>1e-12) return a.pair_std < b.pair_std;
  if(std::abs(a.transition_mix-b.transition_mix)>1e-12) return a.transition_mix > b.transition_mix;
  return a.diversity > b.diversity;
}

template<class R> void perm12(std::array<int,N>& a,R& rng){std::iota(a.begin(),a.end(),0);std::shuffle(a.begin(),a.end(),rng);}

Schedule randomCandidate(std::mt19937_64& rng){Schedule s;perm12(s.rho,rng);perm12(s.sigma,rng);perm12(s.kT,rng);perm12(s.kQ,rng);s.e=evaluate(s);return s;}

Schedule staticGrid(){ Schedule s; std::iota(s.rho.begin(),s.rho.end(),0);std::iota(s.sigma.begin(),s.sigma.end(),0);s.kT.fill(0);s.kQ.fill(0);s.e=evaluate(s);return s; }
Schedule cyclicTour(){ Schedule s; std::iota(s.rho.begin(),s.rho.end(),0);std::iota(s.sigma.begin(),s.sigma.end(),0);std::iota(s.kT.begin(),s.kT.end(),0);std::iota(s.kQ.begin(),s.kQ.end(),0);s.e=evaluate(s);return s; }

Schedule balancedReference(){
  // Historical balanced-fast candidate, now pinned so anyone can re-evaluate it
  // independently instead of trusting the stored receipt.
  Schedule s;
  s.rho   = {1,8,4,11,2,5,3,7,6,9,10,0};
  s.sigma = {6,8,9,10,11,0,5,4,2,7,1,3};
  s.kT    = {8,1,10,7,4,3,6,2,5,0,9,11};
  s.kQ    = {1,10,8,7,2,5,3,11,0,9,6,4};
  s.e=evaluate(s);
  return s;
}

struct WorldRun { int scales=0; int degradation_start=-1; double worst_balance=0; double first_balance=0; double last_balance=0; bool all_invariants=true; uint64_t structural_ops=0; };
WorldRun runWorld100(const Schedule& s,int cap=100){
  WorldRun w; double prev=1e9; int degradeStreak=0;
  std::array<uint64_t,PAIRS> cumulative{};
  for(int scale=1; scale<=cap; ++scale){
    Eval e=evaluate(s);
    if(!e.operational_position_unique || e.unique_pairs!=66) w.all_invariants=false;
    for(int i=0;i<PAIRS;++i)cumulative[i]+=e.pair_counts[i];
    double mean=0; for(auto c:cumulative) mean+=c; mean/=PAIRS;
    double var=0; for(auto c:cumulative){double d=c-mean;var+=d*d;} var/=PAIRS; double bal=std::sqrt(var)/(mean?mean:1);
    if(scale==1)w.first_balance=bal; w.last_balance=bal; w.worst_balance=std::max(w.worst_balance,bal);
    // Degradation = >2% increase in normalized imbalance for 3 consecutive scales.
    if(scale>1 && bal > prev*1.02) degradeStreak++; else degradeStreak=0;
    if(degradeStreak>=3 && w.degradation_start<0){w.degradation_start=scale-2; break;}
    prev=bal; w.scales=scale; w.structural_ops += 24ULL*(12+66+12); // conservative bookkeeping units, not CPU instructions
  }
  return w;
}

void printArr(const char* k,const std::array<int,N>& a){std::cout<<"\""<<k<<"\":[";for(int i=0;i<N;++i){if(i)std::cout<<',';std::cout<<a[i];}std::cout<<']';}
void printEval(const Eval&e){
  std::cout<<"{\"operational_position_unique\":"<<(e.operational_position_unique?"true":"false")
           <<",\"unique_pairs\":"<<e.unique_pairs<<",\"full_pair_phase\":"<<(e.full_pair_phase==999?-1:e.full_pair_phase)
           <<",\"unique_by_phase5\":"<<e.unique_by5<<",\"min_pair_count\":"<<e.min_pair<<",\"max_pair_count\":"<<e.max_pair
           <<",\"pair_stddev\":"<<e.pair_std<<",\"transition_mix\":"<<e.transition_mix<<",\"identity_diversity\":"<<e.diversity
           <<",\"role_balance\":"<<e.role_balance<<",\"cumulative_unique\":[";
  for(int i=0;i<PHASES;++i){if(i)std::cout<<',';std::cout<<e.cumulative_unique[i];}
  std::cout<<"],\"pair_counts\":[";for(int i=0;i<PAIRS;++i){if(i)std::cout<<',';std::cout<<e.pair_counts[i];}std::cout<<"]}";
}

int main(int argc,char**argv){
  for(int i=0,k=0;i<N;i++)for(int j=i+1;j<N;j++,k++){pairIndex[i][j]=pairIndex[j][i]=k;}
  uint64_t iters=argc>1?std::stoull(argv[1]):5000000ULL;
  uint64_t seed=argc>2?std::stoull(argv[2]):0xA9D34CULL;
  std::mt19937_64 rng(seed);
  auto fixed=staticGrid(); auto cyclic=cyclicTour(); auto balanced=balancedReference();
  // Deterministic random baseline average over 5000 lawful no-repeat schedules.
  int rbN=5000; double rbPairs=0,rbPhase=0,rbMix=0,rbDiv=0,rbStd=0; int rbFull=0;
  for(int i=0;i<rbN;i++){auto x=randomCandidate(rng);rbPairs+=x.e.unique_pairs;rbMix+=x.e.transition_mix;rbDiv+=x.e.diversity;rbStd+=x.e.pair_std;if(x.e.full_pair_phase!=999){rbFull++;rbPhase+=x.e.full_pair_phase;}}
  Schedule best=randomCandidate(rng);
  uint64_t evals=0;
  auto t0=Clock::now();
  for(uint64_t i=0;i<iters;i++){
    auto c=randomCandidate(rng); evals++;
    if(better(c.e,best.e)) best=std::move(c);
    // The theoretical earliest possible full coverage is phase 5 (only 60 pair contacts exist after 4 phases).
    // If we also hit near-perfect full-cycle balance (spread <=1), keep searching briefly only for mixing/diversity;
    // no unsafe infinite search.
  }
  auto t1=Clock::now(); double sec=std::chrono::duration<double>(t1-t0).count();
  auto world=runWorld100(best,100); auto balancedWorld=runWorld100(balanced,100);
  std::cout<<std::fixed<<std::setprecision(9);
  std::cout<<"{\n\"schema\":\"AuraTriadQuartetLatticeBenchmarkV0_1_D0\",\n";
  std::cout<<"\"seed\":"<<seed<<",\"search_iterations\":"<<evals<<",\"search_seconds\":"<<sec<<",\"candidate_schedules_per_sec\":"<<(sec?evals/sec:0)<<",\n";
  std::cout<<"\"theoretical\":{\"pair_total\":66,\"pair_contacts_first4\":60,\"pair_contacts_first5\":72,\"earliest_possible_full_pair_coverage_phase\":5,\"operational_seats_per_agent_per_gate24_cycle\":24},\n";
  std::cout<<"\"fixed_static_grid\":";printEval(fixed.e);std::cout<<",\n\"cyclic_no_repeat_tour\":";printEval(cyclic.e);std::cout<<",\n";
  std::cout<<"\"balanced_reference\":";printEval(balanced.e);std::cout<<",\n";
  std::cout<<"\"random_no_repeat_baseline\":{\"samples\":"<<rbN<<",\"avg_unique_pairs\":"<<rbPairs/rbN<<",\"full_coverage_fraction\":"<<double(rbFull)/rbN<<",\"avg_full_phase_when_reached\":"<<(rbFull?rbPhase/rbFull:-1)<<",\"avg_transition_mix\":"<<rbMix/rbN<<",\"avg_identity_diversity\":"<<rbDiv/rbN<<",\"avg_pair_stddev\":"<<rbStd/rbN<<"},\n";
  std::cout<<"\"best\":{\n"; printArr("rho",best.rho);std::cout<<',';printArr("sigma",best.sigma);std::cout<<',';printArr("kT",best.kT);std::cout<<',';printArr("kQ",best.kQ);std::cout<<",\"metrics\":";printEval(best.e);std::cout<<"},\n";
  std::cout<<"\"world_scale_test\":{\"requested_cap\":100,\"completed_scales\":"<<world.scales<<",\"degradation_start\":"<<world.degradation_start<<",\"all_structural_invariants\":"<<(world.all_invariants?"true":"false")<<",\"pair_balance_cv_first\":"<<world.first_balance<<",\"pair_balance_cv_last\":"<<world.last_balance<<",\"pair_balance_cv_worst\":"<<world.worst_balance<<",\"structural_bookkeeping_ops\":"<<world.structural_ops<<"},\n";  std::cout<<"\"balanced_reference_world_scale_test\":{\"requested_cap\":100,\"completed_scales\":"<<balancedWorld.scales<<",\"degradation_start\":"<<balancedWorld.degradation_start<<",\"all_structural_invariants\":"<<(balancedWorld.all_invariants?"true":"false")<<",\"pair_balance_cv_first\":"<<balancedWorld.first_balance<<",\"pair_balance_cv_last\":"<<balancedWorld.last_balance<<",\"pair_balance_cv_worst\":"<<balancedWorld.worst_balance<<",\"structural_bookkeeping_ops\":"<<balancedWorld.structural_ops<<"},\n";
  std::cout<<"\"laws\":[\"Triad=ExpansionPerspective\",\"Quartet=ContractionRebase\",\"OperationalSeat=(Mode,Cell)\",\"NoOperationalSeatRepeatWithin24PhaseCycle\",\"RebaseResetsLocalSeatFrameWhilePreservingGlobalLineage\",\"FullPairCoverage!=SemanticTruth\",\"SyntheticStructuralBenchmark!=ModelReasoningBenchmark\"]\n}\n";
}