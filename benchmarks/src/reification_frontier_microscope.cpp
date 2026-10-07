#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std;

static constexpr size_t BLOCK = 64 * 1024;
static constexpr uint64_t FNV_OFF=1469598103934665603ULL, FNV_PRIME=1099511628211ULL;
uint64_t fnv64(const uint8_t* p,size_t n,uint64_t h=FNV_OFF){for(size_t i=0;i<n;i++){h^=p[i];h*=FNV_PRIME;}return h;}
string hx(uint64_t x){ostringstream o;o<<hex<<setw(16)<<setfill('0')<<x;return o.str();}
size_t vsize(uint64_t x){size_t n=1;while(x>=128){x>>=7;n++;}return n;}
string esc(const string&s){string o; for(unsigned char c:s){if(c=='"')o+="\\\"";else if(c=='\\')o+="\\\\";else if(c=='\n')o+="\\n";else if(c=='\r')o+="\\r";else if(c=='\t')o+="\\t";else if(c<32){char b[7];snprintf(b,sizeof b,"\\u%04x",c);o+=b;}else o+=char(c);} return o;}

double entropy_bits(const vector<uint8_t>&x){if(x.empty())return 0; array<uint64_t,256> c{};for(auto b:x)c[b]++;double H=0,n=x.size();for(auto v:c)if(v){double p=v/n;H-=p*log2(p);}return H;}

struct Patch{uint32_t pos;uint8_t val;};
struct Run{uint32_t len;uint8_t val;};
struct LZToken{bool match;uint32_t len=0,dist=0;vector<uint8_t> lit;};
struct Enc {
 string kind; size_t est=0, program=0,residual=0; uint32_t period=0; uint8_t a=0,b=0;
 vector<uint8_t> raw,base; vector<Patch> patches; vector<Run> runs; vector<LZToken> lz;
};

Enc rawEnc(const vector<uint8_t>&x){Enc e;e.kind="RAW_SOURCE";e.raw=x;e.program=0;e.residual=x.size();e.est=x.size()+8;return e;}
Enc rleEnc(const vector<uint8_t>&x){Enc e;e.kind="RLE";e.est=12;if(x.empty())return e;for(size_t i=0;i<x.size();){size_t j=i+1;while(j<x.size()&&x[j]==x[i]&&j-i<0xffffffffu)j++;e.runs.push_back({(uint32_t)(j-i),x[i]});e.est+=5;i=j;}e.program=4;e.residual=e.est-e.program;return e;}
Enc sparseZeroEnc(const vector<uint8_t>&x){Enc e;e.kind="SPARSE_ZERO";e.est=16;e.program=1;uint32_t last=0;bool first=true;for(uint32_t i=0;i<x.size();i++)if(x[i]){uint32_t d=first?i:i-last;e.patches.push_back({i,x[i]});e.est+=vsize(d)+1;last=i;first=false;}e.residual=e.est-e.program;return e;}
Enc affineEnc(const vector<uint8_t>&x){Enc e;e.kind="AFFINE8_RESIDUAL";e.est=18;e.program=2;if(x.empty())return e;e.b=x[0];e.a=x.size()>1?uint8_t(x[1]-x[0]):0;uint32_t last=0;bool first=true;for(uint32_t i=0;i<x.size();i++){uint8_t pred=uint8_t(uint32_t(e.a)*i+e.b);if(x[i]!=pred){uint32_t d=first?i:i-last;e.patches.push_back({i,x[i]});e.est+=vsize(d)+1;last=i;first=false;}}e.residual=e.est-e.program;return e;}
Enc periodicEnc(const vector<uint8_t>&x){Enc best;best.kind="PERIODIC_RESIDUAL";best.est=numeric_limits<size_t>::max();static const uint32_t P[]={1,2,4,8,16,32,64,128,256,512,1024,2048,4096};for(uint32_t p:P){if(p>x.size())break;Enc e;e.kind="PERIODIC_RESIDUAL";e.period=p;e.base.assign(x.begin(),x.begin()+p);e.program=p;e.est=20+p;uint32_t last=0;bool first=true;for(uint32_t i=p;i<x.size();i++)if(x[i]!=e.base[i%p]){uint32_t d=first?i:i-last;e.patches.push_back({i,x[i]});e.est+=vsize(d)+1;last=i;first=false;}e.residual=e.est-e.program;if(e.est<best.est)best=move(e);}return best;}
Enc prevEnc(const vector<uint8_t>&x,const vector<uint8_t>*prev){Enc e;e.kind="PREV_BLOCK_RESIDUAL";if(!prev||prev->size()!=x.size()){e.est=numeric_limits<size_t>::max();return e;}e.est=20;e.program=8;uint32_t last=0;bool first=true;for(uint32_t i=0;i<x.size();i++)if(x[i]!=(*prev)[i]){uint32_t d=first?i:i-last;e.patches.push_back({i,x[i]});e.est+=vsize(d)+1;last=i;first=false;}e.residual=e.est-e.program;return e;}

static inline uint32_t key4(const vector<uint8_t>&x,size_t i){uint32_t v;memcpy(&v,x.data()+i,4);return v;}
Enc lzEnc(const vector<uint8_t>&x){Enc e;e.kind="LZ_BACKREF";e.est=16;e.program=8;unordered_map<uint32_t,uint32_t> last;last.reserve(x.size()/3+16);vector<uint8_t> lits;auto flush=[&](){if(lits.empty())return;e.est+=5+lits.size();LZToken t;t.match=false;t.len=lits.size();t.lit.swap(lits);e.lz.push_back(move(t));};size_t i=0;while(i<x.size()){size_t best=0,dist=0;if(i+4<=x.size()){uint32_t k=key4(x,i);auto it=last.find(k);if(it!=last.end()){size_t j=it->second;if(i>j && i-j<=0xffffffffu){size_t m=0,cap=min<size_t>(65535,x.size()-i);while(m<cap && j+m<i && x[j+m]==x[i+m])m++; // no overlap expansion, deterministic
if(m>=8){best=m;dist=i-j;}}}last[k]=i;}
if(best>=8){flush();LZToken t;t.match=true;t.len=best;t.dist=dist;e.lz.push_back(t);e.est+=9;for(size_t q=1;q<best && i+q+4<=x.size();q+=4)last[key4(x,i+q)]=i+q;i+=best;}else{lits.push_back(x[i]);i++;if(lits.size()>=65535)flush();}}
flush();e.residual=e.est-e.program;return e;}

vector<uint8_t> decode(const Enc&e,size_t n,const vector<uint8_t>*prev){vector<uint8_t> o; if(e.kind=="RAW_SOURCE")return e.raw;if(e.kind=="RLE"){o.reserve(n);for(auto&r:e.runs)o.insert(o.end(),r.len,r.val);return o;}if(e.kind=="SPARSE_ZERO"){o.assign(n,0);for(auto&p:e.patches)o[p.pos]=p.val;return o;}if(e.kind=="AFFINE8_RESIDUAL"){o.resize(n);for(uint32_t i=0;i<n;i++)o[i]=uint8_t(uint32_t(e.a)*i+e.b);for(auto&p:e.patches)o[p.pos]=p.val;return o;}if(e.kind=="PERIODIC_RESIDUAL"){o.resize(n);for(size_t i=0;i<n;i++)o[i]=e.base[i%e.period];for(auto&p:e.patches)o[p.pos]=p.val;return o;}if(e.kind=="PREV_BLOCK_RESIDUAL"){if(!prev)return {};o=*prev;for(auto&p:e.patches)o[p.pos]=p.val;return o;}if(e.kind=="LZ_BACKREF"){o.reserve(n);for(auto&t:e.lz){if(!t.match)o.insert(o.end(),t.lit.begin(),t.lit.end());else{size_t start=o.size()-t.dist;for(uint32_t q=0;q<t.len;q++)o.push_back(o[start+q]);}}return o;}return {};}

struct FileResult{
 string path;uint64_t bytes=0,source_hash=0,chain_root=0;double entropy=0,ratio=1,residual_fraction=1,analyze_ms=0,reopen_ms=0,reopen_mib_s=0;bool exact=true;
 uint64_t exact_bytes=0,program_bytes=0,residual_bytes=0;size_t blocks=0;unordered_map<string,size_t> kinds;vector<Enc> encs;
};
FileResult analyze(const string&path){ifstream f(path,ios::binary);if(!f)throw runtime_error("OPEN_FAILED:"+path);vector<uint8_t> all((istreambuf_iterator<char>(f)),{});FileResult R;R.path=path;R.bytes=all.size();R.source_hash=fnv64(all.data(),all.size());auto t0=chrono::steady_clock::now();double Hsum=0;vector<uint8_t> prev;for(size_t off=0;off<all.size();off+=BLOCK){size_t n=min(BLOCK,all.size()-off);vector<uint8_t>x(all.begin()+off,all.begin()+off+n);Hsum+=entropy_bits(x)*n;vector<Enc> cands; cands.push_back(rawEnc(x));cands.push_back(rleEnc(x));cands.push_back(sparseZeroEnc(x));cands.push_back(affineEnc(x));cands.push_back(periodicEnc(x));cands.push_back(prevEnc(x,prev.empty()?nullptr:&prev));cands.push_back(lzEnc(x));auto it=min_element(cands.begin(),cands.end(),[](auto&a,auto&b){return a.est<b.est;});Enc w=move(*it);auto dec=decode(w,n,prev.empty()?nullptr:&prev);bool ok=dec==x;R.exact=R.exact&&ok;R.kinds[w.kind]++;R.exact_bytes+=w.est;R.program_bytes+=w.program;R.residual_bytes+=w.residual;uint64_t bh=fnv64(x.data(),x.size(),R.chain_root?R.chain_root:FNV_OFF);R.chain_root=bh;R.encs.push_back(move(w));prev=move(x);R.blocks++;}
auto t1=chrono::steady_clock::now();R.analyze_ms=chrono::duration<double,milli>(t1-t0).count();R.entropy=R.bytes?Hsum/R.bytes:0;R.ratio=R.bytes?double(R.exact_bytes)/R.bytes:1;R.residual_fraction=R.exact_bytes?double(R.residual_bytes)/R.exact_bytes:1;
// timed reopen 3x, dependency-respecting
size_t loops=3;uint64_t sink=0;auto d0=chrono::steady_clock::now();for(size_t rep=0;rep<loops;rep++){vector<uint8_t> p;size_t off=0;for(auto&e:R.encs){size_t n=min(BLOCK,(size_t)R.bytes-off);auto dec=decode(e,n,p.empty()?nullptr:&p);if(dec.size()!=n){R.exact=false;break;}sink^=fnv64(dec.data(),dec.size(),sink? sink:FNV_OFF);p=move(dec);off+=n;}}auto d1=chrono::steady_clock::now();R.reopen_ms=chrono::duration<double,milli>(d1-d0).count()/loops;R.reopen_mib_s=R.reopen_ms>0?(R.bytes/(1024.0*1024.0))/(R.reopen_ms/1000.0):0;if(sink==0x123456789ULL)cerr<<"sink";return R;}

int main(int argc,char**argv){if(argc<2){cerr<<"usage: reification_frontier_microscope FILE...\n";return 2;}vector<FileResult> rs;bool all=true;for(int i=1;i<argc;i++){try{rs.push_back(analyze(argv[i]));all=all&&rs.back().exact;}catch(exception&e){cerr<<e.what()<<"\n";return 3;}}
cout<<"{\n  \"receipt_type\":\"AURA_REIFICATION_FRONTIER_MICROSCOPE_V0_1_D0\",\n  \"block_bytes\":"<<BLOCK<<",\n  \"laws\":[\"ByteExactOrTypedHold\",\"ProgramPlusResidualEqualsReopenableSource\",\"CompressionWinMustBeatSourceFallback\",\"LossyProjectionNotSourceIdentity\",\"PhysicalMediumDoesNotChangeInformationComplexity\"],\n  \"files\":[\n";
for(size_t i=0;i<rs.size();i++){auto&r=rs[i];string cls=r.ratio<0.35?"STRUCTURE_DOMINANT":r.ratio<0.8?"MIXED_REIFIABLE":"RESIDUAL_DOMINANT_SOURCE_FALLBACK";cout<<"    {\"path\":\""<<esc(r.path)<<"\",\"source_bytes\":"<<r.bytes<<",\"fnv64\":\""<<hx(r.source_hash)<<"\",\"reopen_chain_root\":\""<<hx(r.chain_root)<<"\",\"blocks\":"<<r.blocks<<",\"entropy_bits_per_byte\":"<<fixed<<setprecision(5)<<r.entropy<<",\"best_exact_bytes\":"<<r.exact_bytes<<",\"exact_ratio\":"<<setprecision(6)<<r.ratio<<",\"program_bytes\":"<<r.program_bytes<<",\"residual_bytes\":"<<r.residual_bytes<<",\"residual_fraction_of_representation\":"<<r.residual_fraction<<",\"analysis_ms\":"<<setprecision(3)<<r.analyze_ms<<",\"reopen_ms\":"<<r.reopen_ms<<",\"reopen_mib_sec\":"<<r.reopen_mib_s<<",\"exact_reopen\":"<<(r.exact?"true":"false")<<",\"classification\":\""<<cls<<"\",\"representation_counts\":{";vector<pair<string,size_t>> kv(r.kinds.begin(),r.kinds.end());sort(kv.begin(),kv.end());for(size_t j=0;j<kv.size();j++){if(j)cout<<",";cout<<"\""<<kv[j].first<<"\":"<<kv[j].second;}cout<<"}}"<<(i+1<rs.size()?",":"")<<"\n";}
cout<<"  ],\n  \"disposition\":\""<<(all?"PASS_EXACT_REOPEN_MICROSCOPE":"HOLD_RECONSTRUCTION_MISMATCH")<<"\"\n}\n";return all?0:10;}