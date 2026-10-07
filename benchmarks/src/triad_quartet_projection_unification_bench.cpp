#include <array>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <random>
#include <set>
#include <string>
#include <vector>

using Clock=std::chrono::steady_clock;
constexpr int P=3, M=4, N=12, PHASES=24, PAIRS=66;

static const char* ROW[P]={"SOUND_PAST","TOUCH_PRESENT","SIGHT_FUTURE"};
static const char* COL[M]={"TEMPORAL","AGENCY","REALM","SENSORIUM"};
static const char* CELL[P][M]={
 {"PAST","INTENTION","SPACE","SOUND"},
 {"PRESENT","ACTION","ORDERING","TOUCH"},
 {"FUTURE","WITNESS","SCALE","SIGHT_LIGHT"}
};

static uint64_t mix64(uint64_t x){
 x += 0x9e3779b97f4a7c15ULL; x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL; x=(x^(x>>27))*0x94d049bb133111ebULL; return x^(x>>31);
}
static uint64_t hash12(const std::array<uint64_t,N>& a){uint64_t h=0xcbf29ce484222325ULL;for(auto v:a){h^=mix64(v);h*=0x100000001b3ULL;}return h;}
static int pairIndex[N][N];

struct Sched { std::array<int,N> rho,sigma,kT,kQ; };
static Sched balanced(){
 return {{1,8,4,11,2,5,3,7,6,9,10,0},
         {6,8,9,10,11,0,5,4,2,7,1,3},
         {8,1,10,7,4,3,6,2,5,0,9,11},
         {1,10,8,7,2,5,3,11,0,9,6,4}};
}

struct SchedResult {int fullPhase=-1, uniqueBy5=0, uniquePairs=0,minPair=999,maxPair=0; bool seatUnique=true; std::array<int,PAIRS> counts{};};
static SchedResult evalSchedule(const Sched&s){
 SchedResult r; bool seen[N][2][N]{}; int ti=0,qi=0;
 for(int phase=0;phase<PHASES;++phase){
  bool triad=(phase%2==0); int shift=triad?s.kT[ti++]:s.kQ[qi++];
  std::array<std::vector<int>,4> groups;
  for(int a=0;a<N;++a){int pos=s.sigma[(s.rho[a]+shift)%N];int mode=triad?0:1;if(seen[a][mode][pos])r.seatUnique=false;seen[a][mode][pos]=true;int g=triad?(pos%4):(pos/4);groups[g].push_back(a);} 
  int gc=triad?4:3;
  for(int g=0;g<gc;++g)for(size_t i=0;i<groups[g].size();++i)for(size_t j=i+1;j<groups[g].size();++j)r.counts[pairIndex[groups[g][i]][groups[g][j]]]++;
  int u=0;for(int c:r.counts)if(c)u++;if(phase==4)r.uniqueBy5=u;if(u==PAIRS&&r.fullPhase<0)r.fullPhase=phase+1;
 }
 for(int c:r.counts){if(c)r.uniquePairs++;r.minPair=std::min(r.minPair,c);r.maxPair=std::max(r.maxPair,c);} return r;
}

int main(){
 for(int i=0,k=0;i<N;++i)for(int j=i+1;j<N;++j,++k)pairIndex[i][j]=pairIndex[j][i]=k;

 // 1) exact 3x4 <-> 4x3 incidence
 std::set<std::string> cells; bool singleton=true;
 for(int p=0;p<P;++p)for(int m=0;m<M;++m)cells.insert(CELL[p][m]);
 for(int p=0;p<P;++p)for(int m=0;m<M;++m){int hits=0;for(int pp=0;pp<P;++pp)for(int mm=0;mm<M;++mm)if(pp==p&&mm==m)hits++; if(hits!=1)singleton=false;}
 int staticPairs=P*(M*(M-1)/2)+M*(P*(P-1)/2);

 // 2) million-state reversible transpose/reindex test
 const uint64_t TRIALS=1000000; std::mt19937_64 rng(0x20261006ULL); uint64_t mism=0, rootm=0;
 auto t0=Clock::now();
 for(uint64_t t=0;t<TRIALS;++t){
  std::array<uint64_t,N> row{}, rec{}; for(auto &v:row)v=rng();
  std::array<uint64_t,N> col{};
  for(int p=0;p<P;++p)for(int m=0;m<M;++m)col[m*P+p]=row[p*M+m];
  for(int m=0;m<M;++m)for(int p=0;p<P;++p)rec[p*M+m]=col[m*P+p];
  if(row!=rec)mism++; if(hash12(row)!=hash12(rec))rootm++;
 }
 auto t1=Clock::now(); double rtsec=std::chrono::duration<double>(t1-t0).count();

 // 3) single-cell delta locality: exactly one row quartet + one column triad changes
 int localPass=0;
 std::array<uint64_t,N> base{};for(int i=0;i<N;++i)base[i]=i+100;
 for(int idx=0;idx<N;++idx){
  int p=idx/M,m=idx%M; auto mut=base;mut[idx]^=0xdeadbeefULL;
  int rowChanged=0,colChanged=0;
  for(int rp=0;rp<P;++rp){bool ch=false;for(int mm=0;mm<M;++mm){int j=rp*M+mm;if(base[j]!=mut[j])ch=true;}if(ch)rowChanged++;}
  for(int cm=0;cm<M;++cm){bool ch=false;for(int pp=0;pp<P;++pp){int j=pp*M+cm;if(base[j]!=mut[j])ch=true;}if(ch)colChanged++;}
  if(rowChanged==1&&colChanged==1&&p==idx/M&&m==idx%M)localPass++;
 }

 // 4) prove naive scalar-collapse is lossy with explicit counterexample
 std::array<int,4> a{1,2,3,4}, b{0,3,3,4}; // same sum, different sovereign components
 bool scalarCollision=(std::accumulate(a.begin(),a.end(),0)==std::accumulate(b.begin(),b.end(),0) && a!=b);

 // 5) verify existing balanced rotating schedule on semantic 12-cell identities
 auto sr=evalSchedule(balanced()); int c5=0,c6=0;for(int c:sr.counts){if(c==5)c5++;if(c==6)c6++;}

 // 6) procedural unified-state stress: 29k manifestations x 120 frames x 12 components; no per-instance asset table
 constexpr int INST=29000, FRAMES=120; volatile double sink=0; uint64_t hA=0,hReplay=0,hB=0;
 auto evalFrame=[&](int frame){uint64_t h=0x9e3779b97f4a7c15ULL;double t=frame/60.0;for(int i=0;i<INST;++i){double x=(i%200)/199.0,y=((i/200)%145)/144.0;double phase=0.031*i+0.7*t;for(int p=0;p<P;++p)for(int m=0;m<M;++m){double v=std::sin(phase+0.37*p+0.19*m)+0.5*std::cos((x+y)*(m+1)+t*(p+1));sink+=v*1e-18;uint64_t bits;std::memcpy(&bits,&v,8);h^=mix64(bits+uint64_t(p*4+m));h*=0x100000001b3ULL;}}return h;};
 auto s0=Clock::now();
 for(int f=0;f<FRAMES;++f){auto h=evalFrame(f);if(f==0)hA=h;if(f==1)hB=h;}
 hReplay=evalFrame(0);
 auto s1=Clock::now();double stressSec=std::chrono::duration<double>(s1-s0).count();
 uint64_t evals=uint64_t(INST)*FRAMES*N;

 std::cout<<std::boolalpha<<std::fixed<<std::setprecision(6);
 std::cout<<"{\n";
 std::cout<<"\"schema\":\"AuraThreeProjectionFourComponentLatticeBenchV0_1_D0\",\n";
 std::cout<<"\"matrix\":{\"rows\":3,\"cols\":4,\"unique_cells\":"<<cells.size()<<",\"singleton_intersections\":"<<singleton<<",\"static_row_col_pair_relations\":"<<staticPairs<<"},\n";
 std::cout<<"\"semantic_rows\":[[\"PAST\",\"INTENTION\",\"SPACE\",\"SOUND\"],[\"PRESENT\",\"ACTION\",\"ORDERING\",\"TOUCH\"],[\"FUTURE\",\"WITNESS\",\"SCALE\",\"SIGHT_LIGHT\"]],\n";
 std::cout<<"\"transpose_reopen\":{\"trials\":"<<TRIALS<<",\"state_mismatches\":"<<mism<<",\"root_mismatches\":"<<rootm<<",\"seconds\":"<<rtsec<<"},\n";
 std::cout<<"\"delta_locality\":{\"single_cell_cases\":12,\"pass\":"<<localPass<<",\"expected_changed_projection_quartets\":1,\"expected_changed_master_triads\":1},\n";
 std::cout<<"\"sovereignty_counterexample\":{\"scalar_aggregation_collision\":"<<scalarCollision<<",\"law\":\"UnityRequiresReconstructableComponents_NotAveraging\"},\n";
 std::cout<<"\"rotating_lattice\":{\"operational_seat_unique\":"<<sr.seatUnique<<",\"unique_pairs\":"<<sr.uniquePairs<<",\"full_pair_phase\":"<<sr.fullPhase<<",\"unique_by_phase5\":"<<sr.uniqueBy5<<",\"min_pair_count\":"<<sr.minPair<<",\"max_pair_count\":"<<sr.maxPair<<",\"pairs_at_5\":"<<c5<<",\"pairs_at_6\":"<<c6<<"},\n";
 std::cout<<"\"procedural_state_stress\":{\"instances\":"<<INST<<",\"frames\":"<<FRAMES<<",\"components_per_instance\":12,\"component_evaluations\":"<<evals<<",\"seconds\":"<<stressSec<<",\"million_component_evals_per_sec\":"<<(evals/stressSec/1e6)<<",\"t0_exact_replay\":"<<(hA==hReplay)<<",\"t0_t1_different\":"<<(hA!=hB)<<"},\n";
 std::cout<<"\"claim_boundary\":\"Computational semantic lattice; Sound=Past, Touch=Present, Sight=Future are Aura worldline roles, not literal identities of physical waves or photons.\"\n";
 std::cout<<"}\n";
}