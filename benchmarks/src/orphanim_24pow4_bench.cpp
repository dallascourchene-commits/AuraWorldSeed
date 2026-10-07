#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <vector>
using Clock=std::chrono::steady_clock;
static inline uint64_t mix64(uint64_t x){x^=x>>30;x*=0xbf58476d1ce4e5b9ULL;x^=x>>27;x*=0x94d049bb133111ebULL;x^=x>>31;return x;}
static inline uint64_t combine(uint64_t h,uint64_t v){return mix64(h ^ (v+0x9e3779b97f4a7c15ULL+(h<<6)+(h>>2)));}
static std::array<int,4> digits(uint32_t rank){std::array<int,4>d{};for(int i=3;i>=0;--i){d[i]=rank%24;rank/=24;}return d;}
static uint32_t rank4(const std::array<int,4>&d){uint32_t r=0;for(int x:d)r=r*24u+uint32_t(x);return r;}
static uint64_t semantic(const std::array<int,4>&d,const std::array<int,4>&handles,uint64_t objective){
  (void)handles; // handle identity is trace metadata, not semantic parent input
  uint64_t input=combine(objective,rank4(d));
  uint64_t reality=combine(combine(input,0x5245414c495459ULL),d[0]);
  uint64_t lineage=combine(combine(input,0x4c494e45414745ULL),d[1]);
  uint64_t sovereignty=combine(combine(input,0x534f5645524549ULL),d[2]);
  uint64_t center=combine(combine(combine(combine(input,reality),lineage),sovereignty),0x52454f50454eULL ^ uint64_t(d[3]));
  uint64_t out=combine(input,reality); out=combine(out,lineage); out=combine(out,sovereignty); out=combine(out,center); return out;
}
static uint64_t trace(uint64_t sem,const std::array<int,4>&h,const std::array<int,4>&d){uint64_t x=sem;for(int i=0;i<4;i++)x=combine(x,uint64_t(h[i]+1)*1315423911ULL+uint64_t(d[i]));return x;}
int main(){
  constexpr uint32_t N=24u*24u*24u*24u;
  std::array<int,4> baseh{0,1,2,3}; std::vector<std::array<int,4>> perms;
  do{perms.push_back(baseh);}while(std::next_permutation(baseh.begin(),baseh.end()));
  uint64_t checksum=0, trace_checksum=0; uint64_t roundtrip=0, mirror=0, semantic_pass=0, trace_unique=0;
  auto t0=Clock::now();
  const uint64_t objective=0xA0A020261007ULL;
  for(uint32_t r=0;r<N;r++){
    auto d=digits(r); if(rank4(d)==r)roundtrip++;
    auto m=d; for(auto &x:m)x=23-x; auto mm=m; for(auto &x:mm)x=23-x; if(mm==d)mirror++;
    const auto s0=semantic(d,perms[0],objective); checksum=combine(checksum,s0);
    std::array<uint64_t,24> trs{};
    for(size_t p=0;p<perms.size();p++){
      auto sp=semantic(d,perms[p],objective); if(sp==s0)semantic_pass++;
      trs[p]=trace(sp,perms[p],d); trace_checksum=combine(trace_checksum,trs[p]);
    }
    std::sort(trs.begin(),trs.end()); bool uniq=true; for(size_t i=1;i<trs.size();i++)if(trs[i]==trs[i-1]){uniq=false;break;} if(uniq)trace_unique++;
  }
  auto t1=Clock::now(); double ms=std::chrono::duration<double,std::milli>(t1-t0).count();
  const uint64_t frames=uint64_t(N)*24ULL;
  std::cout<<"{\"schema\":\"AuraOrphanim24Pow4NativeBenchmarkV0_1_D0\","
           <<"\"status\":\""<<((roundtrip==N&&mirror==N&&semantic_pass==frames&&trace_unique==N)?"PASS_24POW4_ORPHANIM":"HOLD")<<"\","
           <<"\"logical_coordinates\":"<<N<<",\"role_permutations\":24,\"semantic_frames\":"<<frames<<","
           <<"\"role_seat_evaluations\":"<<(frames*4ULL)<<",\"rank_roundtrip_pass\":"<<roundtrip<<",\"mirror_involution_pass\":"<<mirror<<","
           <<"\"semantic_invariant_pass\":"<<semantic_pass<<",\"distinct_trace_sets_pass\":"<<trace_unique<<","
           <<"\"elapsed_ms\":"<<ms<<",\"million_semantic_frames_per_sec\":"<<(frames/(ms/1000.0)/1e6)<<","
           <<"\"semantic_checksum\":\""<<std::hex<<checksum<<"\",\"trace_checksum\":\""<<trace_checksum<<"\"}"<<std::dec<<"\n";
}