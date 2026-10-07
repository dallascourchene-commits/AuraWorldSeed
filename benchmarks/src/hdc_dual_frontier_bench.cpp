#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <string>
#include <vector>

using Clock = std::chrono::steady_clock;
static constexpr int D = 8192;
static constexpr int K = 1024;
static constexpr int WORDS = D / 64;
static constexpr float PI_F = 3.14159265358979323846f;
static constexpr int SWEEPS[6] = {2,4,8,16,32,64};

struct SplitMix64 {
    uint64_t s;
    explicit SplitMix64(uint64_t seed): s(seed) {}
    uint64_t next() {
        uint64_t z = (s += 0x9e3779b97f4a7c15ULL);
        z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
        z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
        return z ^ (z >> 31);
    }
    double u01() { return (next() >> 11) * (1.0 / 9007199254740992.0); }
    float gaussian() {
        double u1 = std::max(u01(), 1e-15), u2 = u01();
        return (float)(std::sqrt(-2.0 * std::log(u1)) * std::cos(2.0 * M_PI * u2));
    }
};

static double ms_since(Clock::time_point t0) {
    return std::chrono::duration<double,std::milli>(Clock::now()-t0).count();
}

static void normalize(std::vector<float>& x) {
    double ss=0.0; for(float v:x) ss += (double)v*v;
    double n=std::sqrt(ss); if(n==0) return;
    float inv=(float)(1.0/n); for(float& v:x) v*=inv;
}
static float dot(const float* a, const float* b) {
    double s=0.0;
    #pragma GCC ivdep
    for(int i=0;i<D;i++) s += (double)a[i]*b[i];
    return (float)s;
}
static float cosine(const std::vector<float>& a, const std::vector<float>& b) {
    double ab=0,aa=0,bb=0;
    for(int i=0;i<D;i++){ab+=(double)a[i]*b[i];aa+=(double)a[i]*a[i];bb+=(double)b[i]*b[i];}
    return (float)(ab/std::sqrt(aa*bb));
}

static void fft(std::vector<std::complex<float>>& a, bool invert) {
    const int n=(int)a.size();
    for(int i=1,j=0;i<n;i++){
        int bit=n>>1;
        for(;j&bit;bit>>=1) j^=bit;
        j^=bit;
        if(i<j) std::swap(a[i],a[j]);
    }
    for(int len=2;len<=n;len<<=1){
        float ang = 2.0f*PI_F/len*(invert?1.0f:-1.0f);
        std::complex<float> wlen(std::cos(ang),std::sin(ang));
        for(int i=0;i<n;i+=len){
            std::complex<float> w(1,0);
            for(int j=0;j<len/2;j++){
                auto u=a[i+j], v=a[i+j+len/2]*w;
                a[i+j]=u+v; a[i+j+len/2]=u-v; w*=wlen;
            }
        }
    }
    if(invert){ float inv=1.0f/n; for(auto& z:a) z*=inv; }
}

using Spectrum = std::vector<std::complex<float>>;
static Spectrum spectrum(const std::vector<float>& x){
    Spectrum X(D); for(int i=0;i<D;i++) X[i]=std::complex<float>(x[i],0); fft(X,false); return X;
}
static std::vector<float> from_spectrum(Spectrum X){
    fft(X,true); std::vector<float> x(D); for(int i=0;i<D;i++)x[i]=X[i].real(); return x;
}
static std::vector<float> conv_from_spectra(const Spectrum& A,const Spectrum& B){
    Spectrum C(D); for(int i=0;i<D;i++)C[i]=A[i]*B[i]; return from_spectrum(std::move(C));
}
static std::vector<float> circular_conv(const std::vector<float>& a,const std::vector<float>& b){
    auto A=spectrum(a),B=spectrum(b); return conv_from_spectra(A,B);
}
static std::vector<float> involution(const std::vector<float>& b){
    std::vector<float> r(D); r[0]=b[0]; for(int i=1;i<D;i++)r[i]=b[D-i]; return r;
}
static std::vector<float> direct_conv_reference(const std::vector<float>& a,const std::vector<float>& b){
    std::vector<float> c(D); constexpr int mask=D-1;
    for(int n=0;n<D;n++){
        double s=0.0;
        for(int i=0;i<D;i++) s += (double)a[i]*b[(n-i)&mask];
        c[n]=(float)s;
    }
    return c;
}
static std::vector<float> gaussian_unit_vector(SplitMix64& rng){
    std::vector<float> x(D); float scale=1.0f/std::sqrt((float)D);
    for(float& v:x) v=rng.gaussian()*scale; normalize(x); return x;
}
static std::vector<float> unitary_role(SplitMix64& rng){
    Spectrum X(D);
    X[0]=std::complex<float>((rng.next()&1)?1.0f:-1.0f,0);
    X[D/2]=std::complex<float>((rng.next()&1)?1.0f:-1.0f,0);
    for(int k=1;k<D/2;k++){
        float phase=(float)(2.0*M_PI*rng.u01());
        std::complex<float> z(std::cos(phase),std::sin(phase));
        X[k]=z; X[D-k]=std::conj(z);
    }
    auto x=from_spectrum(std::move(X)); normalize(x); return x;
}

struct HRRCodebook {
    std::vector<float> data;
    std::vector<Spectrum> spec;
    HRRCodebook(): data((size_t)K*D), spec(K) {}
    const float* ptr(int j) const { return data.data()+(size_t)j*D; }
};

struct RetrievalStats {
    int top1=0;
    float target=0, mean_abs=0, sigma_abs=0, snr=0;
};
static RetrievalStats hrr_retrieve(const std::vector<float>& q,const HRRCodebook& cb,int target_idx){
    std::vector<float> qn=q; normalize(qn);
    float best=-std::numeric_limits<float>::infinity(); int bestj=-1;
    double sum=0,sum2=0; int n=0; float target=0;
    for(int j=0;j<K;j++){
        float s=dot(qn.data(),cb.ptr(j));
        if(j==target_idx) target=s; else {double a=std::fabs((double)s);sum+=a;sum2+=a*a;n++;}
        if(s>best){best=s;bestj=j;}
    }
    double mean=sum/n, var=std::max(0.0,sum2/n-mean*mean), sig=std::sqrt(var);
    return {bestj==target_idx,target,(float)mean,(float)sig,(float)((target-mean)/(sig+1e-12))};
}

using BVec = std::array<uint64_t,WORDS>;
static BVec bsc_random(SplitMix64& rng){BVec x{};for(auto& w:x)w=rng.next();return x;}
static BVec bsc_xor(const BVec&a,const BVec&b){BVec c{};for(int i=0;i<WORDS;i++)c[i]=a[i]^b[i];return c;}
static int hamming(const BVec&a,const BVec&b){int h=0;for(int i=0;i<WORDS;i++)h+=std::popcount(a[i]^b[i]);return h;}
static float bipolar_sim(const BVec&a,const BVec&b){return 1.0f-2.0f*((float)hamming(a,b)/D);}
static BVec bsc_permute(const BVec& x,int shift){
    shift%=D; if(shift<0)shift+=D; if(shift==0)return x;
    int ws=shift/64, bs=shift%64; BVec y{};
    for(int d=0;d<WORDS;d++){
        int s0=(d-ws+WORDS)%WORDS;
        if(bs==0)y[d]=x[s0];
        else {int s1=(s0-1+WORDS)%WORDS; y[d]=(x[s0]<<bs)|(x[s1]>>(64-bs));}
    }
    return y;
}
static BVec bsc_bundle_majority(const std::vector<BVec>& xs,int k,const BVec& tie){
    BVec out{};
    for(int w=0;w<WORDS;w++){
        uint64_t ow=0;
        for(int b=0;b<64;b++){
            int c=0; uint64_t m=1ULL<<b;
            for(int i=0;i<k;i++) c += (xs[i][w]&m)?1:0;
            bool bit = c*2>k ? true : (c*2<k ? false : ((tie[w]&m)!=0));
            if(bit) ow|=m;
        }
        out[w]=ow;
    }
    return out;
}
struct BSCCodebook { std::vector<BVec> v; BSCCodebook():v(K){} };
static RetrievalStats bsc_retrieve(const BVec&q,const BSCCodebook&cb,int target_idx){
    float best=-2; int bestj=-1; double sum=0,sum2=0;int n=0;float target=0;
    for(int j=0;j<K;j++){
        float s=bipolar_sim(q,cb.v[j]);
        if(j==target_idx)target=s; else {double a=std::fabs((double)s);sum+=a;sum2+=a*a;n++;}
        if(s>best){best=s;bestj=j;}
    }
    double mean=sum/n,var=std::max(0.0,sum2/n-mean*mean),sig=std::sqrt(var);
    return{bestj==target_idx,target,(float)mean,(float)sig,(float)((target-mean)/(sig+1e-12))};
}

struct SweepRow {int k; double top1_rate; double target_mean; double distractor_abs_mean; double snr_mean; double snr_min;};
struct HRRRun {std::vector<SweepRow> rows; double bind_ops=0,bind_cached_ops=0,unbind_ops=0,cleanup_ops=0;};
struct BSCRun {std::vector<SweepRow> rows; double bind_ops=0,unbind_ops=0,cleanup_ops=0,permute_ops=0;};

static HRRRun run_hrr(const HRRCodebook&cb,const std::vector<std::vector<float>>&roles,const std::vector<Spectrum>&roleSpec){
    HRRRun R; std::vector<std::vector<float>> bound(64); std::vector<Spectrum> boundSpec(64);
    for(int i=0;i<64;i++){bound[i]=conv_from_spectra(roleSpec[i],cb.spec[i]);boundSpec[i]=spectrum(bound[i]);}
    for(int kk:SWEEPS){
        std::vector<float> M(D,0); for(int i=0;i<kk;i++)for(int d=0;d<D;d++)M[d]+=bound[i][d]; normalize(M);
        auto MS=spectrum(M); int hits=0; double tm=0,dm=0,sm=0,smin=1e300;
        for(int i=0;i<kk;i++){
            Spectrum Q(D); for(int d=0;d<D;d++)Q[d]=MS[d]*std::conj(roleSpec[i][d]);
            auto q=from_spectrum(std::move(Q)); auto st=hrr_retrieve(q,cb,i);
            hits+=st.top1;tm+=st.target;dm+=st.mean_abs;sm+=st.snr;smin=std::min(smin,(double)st.snr);
        }
        R.rows.push_back({kk,(double)hits/kk,tm/kk,dm/kk,sm/kk,smin});
    }
    // Timed cold bind/unbind include forward FFTs.
    volatile float sink=0; int reps=12;
    auto t=Clock::now(); for(int r=0;r<reps;r++){auto c=circular_conv(roles[r%64],std::vector<float>(cb.ptr(r%K),cb.ptr(r%K)+D)); sink+=c[r%D];} double dt=ms_since(t);R.bind_ops=reps/(dt/1000.0);
    t=Clock::now(); for(int r=0;r<reps;r++){auto inv=involution(roles[r%64]);auto c=circular_conv(bound[r%64],inv);sink+=c[(r+3)%D];}dt=ms_since(t);R.unbind_ops=reps/(dt/1000.0);
    // Cached-spectrum bind: multiply + inverse FFT.
    reps=64;t=Clock::now();for(int r=0;r<reps;r++){auto c=conv_from_spectra(roleSpec[r%64],cb.spec[r%K]);sink+=c[(r+5)%D];}dt=ms_since(t);R.bind_cached_ops=reps/(dt/1000.0);
    // Cleanup sweeps.
    auto q=bound[0];normalize(q);reps=6;t=Clock::now();for(int r=0;r<reps;r++){float best=-9;for(int j=0;j<K;j++)best=std::max(best,dot(q.data(),cb.ptr(j)));sink+=best;}dt=ms_since(t);R.cleanup_ops=reps/(dt/1000.0);
    if(sink==123456.0f)std::cerr<<"sink";
    return R;
}

static BSCRun run_bsc(const BSCCodebook&cb,const std::vector<BVec>&roles,const BVec&tie){
    BSCRun R; std::vector<BVec> bound(64);for(int i=0;i<64;i++)bound[i]=bsc_xor(roles[i],cb.v[i]);
    for(int kk:SWEEPS){
        BVec M=bsc_bundle_majority(bound,kk,tie);int hits=0;double tm=0,dm=0,sm=0,smin=1e300;
        for(int i=0;i<kk;i++){auto q=bsc_xor(M,roles[i]);auto st=bsc_retrieve(q,cb,i);hits+=st.top1;tm+=st.target;dm+=st.mean_abs;sm+=st.snr;smin=std::min(smin,(double)st.snr);}
        R.rows.push_back({kk,(double)hits/kk,tm/kk,dm/kk,sm/kk,smin});
    }
    volatile uint64_t sink=0;int reps=300000;auto t=Clock::now();for(int r=0;r<reps;r++){auto c=bsc_xor(roles[r&63],cb.v[r&(K-1)]);sink^=c[r&(WORDS-1)];}double dt=ms_since(t);R.bind_ops=reps/(dt/1000.0);
    t=Clock::now();for(int r=0;r<reps;r++){auto c=bsc_xor(bound[r&63],roles[r&63]);sink^=c[(r+1)&(WORDS-1)];}dt=ms_since(t);R.unbind_ops=reps/(dt/1000.0);
    reps=1000;t=Clock::now();for(int r=0;r<reps;r++){int best=1e9;auto&q=bound[r&63];for(int j=0;j<K;j++)best=std::min(best,hamming(q,cb.v[j]));sink^=(uint64_t)best;}dt=ms_since(t);R.cleanup_ops=reps/(dt/1000.0);
    reps=300000;t=Clock::now();for(int r=0;r<reps;r++){auto p=bsc_permute(roles[r&63],r&8191);sink^=p[(r+7)&(WORDS-1)];}dt=ms_since(t);R.permute_ops=reps/(dt/1000.0);
    if(sink==0xdeadbeefULL)std::cerr<<"sink";
    return R;
}

static std::string pass(bool x){return x?"PASS":"HOLD";}
static std::string jf(double x){std::ostringstream o;o<<std::fixed<<std::setprecision(6)<<x;return o.str();}
static void rows_json(std::ostream&o,const std::vector<SweepRow>&rows){
    o<<"[";for(size_t i=0;i<rows.size();i++){if(i)o<<",";auto&r=rows[i];o<<"{\"k\":"<<r.k<<",\"top1_rate\":"<<jf(r.top1_rate)<<",\"target_similarity_mean\":"<<jf(r.target_mean)<<",\"distractor_abs_mean\":"<<jf(r.distractor_abs_mean)<<",\"snr_mean\":"<<jf(r.snr_mean)<<",\"snr_min\":"<<jf(r.snr_min)<<"}";}o<<"]";
}

int main(int argc,char**argv){
    bool literal=true; if(argc>1 && std::string(argv[1])=="--statistical-orthogonality")literal=false;
    auto all0=Clock::now();SplitMix64 rng(0xa17a20261007ULL ^ 0x9d6f47a3b25c1e77ULL);

    HRRCodebook hcb;
    for(int j=0;j<K;j++){
        auto x=gaussian_unit_vector(rng);std::copy(x.begin(),x.end(),hcb.data.begin()+(size_t)j*D);hcb.spec[j]=spectrum(x);
    }
    std::vector<std::vector<float>> rolesG(64),rolesU(64);std::vector<Spectrum> specG(64),specU(64);
    for(int i=0;i<64;i++){rolesG[i]=gaussian_unit_vector(rng);specG[i]=spectrum(rolesG[i]);rolesU[i]=unitary_role(rng);specU[i]=spectrum(rolesU[i]);}
    BSCCodebook bcb;for(int j=0;j<K;j++)bcb.v[j]=bsc_random(rng);std::vector<BVec>broles(64);for(auto&x:broles)x=bsc_random(rng);BVec tie=bsc_random(rng);

    // FFT vs O(D^2) reference once.
    auto ref0=Clock::now();std::vector<float> a0(hcb.ptr(0),hcb.ptr(0)+D),b0(hcb.ptr(1),hcb.ptr(1)+D);
    auto cref=direct_conv_reference(a0,b0);double ref_ms=ms_since(ref0);auto cfft=circular_conv(a0,b0);double maxerr=0;for(int i=0;i<D;i++)maxerr=std::max(maxerr,std::fabs((double)cref[i]-cfft[i]));float ref_rho=cosine(cref,cfft);bool fft_ref=(ref_rho>0.999999f && maxerr<2e-4);

    std::vector<float> e(D,0);e[0]=1;auto aid=circular_conv(a0,e);float idrho=cosine(a0,aid);bool hrr_identity=idrho>0.9999f;
    auto bx=bsc_random(rng),by=bsc_random(rng);auto bback=bsc_xor(bsc_xor(bx,by),by);bool bsc_self=(hamming(bx,bback)==0);
    auto p=bsc_permute(bx,137),pb=bsc_permute(p,D-137);bool perm_inverse=(hamming(bx,pb)==0);

    // Orthogonality: compare all 1023 non-reference codebook entries to item 0.
    const double hrr_bound=4.0/std::sqrt((double)D);int hrr_ok=0,bsc_ok=0;double hrr_max=0,bsc_min=1,bsc_max=0,hrr_abs_sum=0,bsc_dist_sum=0;
    for(int j=1;j<K;j++){
        float s=dot(hcb.ptr(0),hcb.ptr(j));double aa=std::fabs((double)s);hrr_abs_sum+=aa;hrr_max=std::max(hrr_max,aa);if(aa<hrr_bound)hrr_ok++;
        double dist=(double)hamming(bcb.v[0],bcb.v[j])/D;bsc_dist_sum+=dist;bsc_min=std::min(bsc_min,dist);bsc_max=std::max(bsc_max,dist);if(dist>=0.485&&dist<=0.515)bsc_ok++;
    }
    double hrr_frac=(double)hrr_ok/(K-1),bsc_frac=(double)bsc_ok/(K-1);
    bool ortho_literal=(hrr_ok==K-1 && bsc_ok==K-1);
    // Statistical policy: >=99% within nominal per-pair bounds AND ensemble means close to theory.
    bool ortho_stat=(hrr_frac>=0.99 && bsc_frac>=0.99 && (hrr_abs_sum/(K-1))<0.02 && std::fabs(bsc_dist_sum/(K-1)-0.5)<0.002);
    bool ortho = literal?ortho_literal:ortho_stat;

    auto hrrG=run_hrr(hcb,rolesG,specG);auto hrrU=run_hrr(hcb,rolesU,specU);auto bsc=run_bsc(bcb,broles,tie);
    auto row=[&](const std::vector<SweepRow>&rs,int k)->const SweepRow&{for(auto&r:rs)if(r.k==k)return r;return rs[0];};
    bool top1k8 = row(hrrG.rows,8).top1_rate==1.0 && row(bsc.rows,8).top1_rate==1.0;
    bool cap64 = row(hrrG.rows,64).snr_min>=1.0 && row(bsc.rows,64).snr_min>=1.0;
    bool allpass=fft_ref&&hrr_identity&&bsc_self&&perm_inverse&&top1k8&&ortho&&cap64;
    double elapsed=ms_since(all0);

#ifdef __AVX512F__
    const char* simd="AVX512_NATIVE";
#elif defined(__AVX2__)
    const char* simd="AVX2_NATIVE";
#elif defined(__AVX__)
    const char* simd="AVX_NATIVE";
#else
    const char* simd="NATIVE_SCALAR_OR_AUTOVECTORIZED";
#endif

    std::ostringstream o;
    o<<"{";
    o<<"\"receipt_type\":\"AURA_HDC_DUAL_FRONTIER_V0_2_D0\",";
    o<<"\"carrier_metadata\":{\"dimensions\":"<<D<<",\"codebook_size\":"<<K<<",\"simd_vectorization\":\""<<simd<<"\",\"compiler_flags\":\"-O3 -march=native -std=c++20\",\"no_external_dependencies\":true},";
    o<<"\"policy\":{\"orthogonality\":\""<<(literal?"LITERAL_ALL_1023":"STATISTICALLY_CALIBRATED_99_PERCENT")<<"\",\"NativeSpeed!=SemanticPrecision\":true,\"ContinuousDynamics!=BitwiseSpatter\":true},";
    o<<"\"falsifiers\":{";
    o<<"\"HRR_FFT_REFERENCE\":\""<<pass(fft_ref)<<"\",\"HRR_IDENTITY\":\""<<pass(hrr_identity)<<"\",\"BSC_SELF_INVERSE\":\""<<pass(bsc_self)<<"\",\"BSC_PERMUTE_INVERSE\":\""<<pass(perm_inverse)<<"\",\"TOP1_RECOVERY_K8\":\""<<pass(top1k8)<<"\",\"ORTHOGONAL_NOISE_FLOOR\":\""<<pass(ortho)<<"\",\"CAPACITY_BOUND_K64\":\""<<pass(cap64)<<"\"},";
    o<<"\"evidence\":{";
    o<<"\"hrr_identity_rho\":"<<jf(idrho)<<",\"fft_reference_rho\":"<<jf(ref_rho)<<",\"fft_reference_max_abs_error\":"<<jf(maxerr)<<",\"direct_d2_reference_elapsed_ms\":"<<jf(ref_ms)<<",";
    o<<"\"orthogonality\":{\"hrr_bound_abs_rho\":"<<jf(hrr_bound)<<",\"hrr_fraction_within\":"<<jf(hrr_frac)<<",\"hrr_max_abs_rho\":"<<jf(hrr_max)<<",\"hrr_mean_abs_rho\":"<<jf(hrr_abs_sum/(K-1))<<",\"bsc_fraction_within\":"<<jf(bsc_frac)<<",\"bsc_min_hamming_fraction\":"<<jf(bsc_min)<<",\"bsc_max_hamming_fraction\":"<<jf(bsc_max)<<",\"bsc_mean_hamming_fraction\":"<<jf(bsc_dist_sum/(K-1))<<"},";
    o<<"\"gaussian_vs_unitary_hrr_note\":\"Primary HRR falsifier uses iid Gaussian unit vectors per task. Fourier-unitary roles are reported as a diagnostic because involution is an exact inverse only for unitary spectra.\"},";
    o<<"\"benchmarks\":{";
    o<<"\"hrr\":{\"bind_throughput_ops_sec\":"<<jf(hrrG.bind_ops)<<",\"bind_cached_spectral_ops_sec\":"<<jf(hrrG.bind_cached_ops)<<",\"unbind_throughput_ops_sec\":"<<jf(hrrG.unbind_ops)<<",\"cleanup_sweep_ops_sec\":"<<jf(hrrG.cleanup_ops)<<",\"recovery_top1_rate_k8\":"<<jf(row(hrrG.rows,8).top1_rate)<<",\"recovery_top1_rate_k32\":"<<jf(row(hrrG.rows,32).top1_rate)<<",\"sweep\":";rows_json(o,hrrG.rows);o<<"},";
    o<<"\"hrr_unitary_diagnostic\":{\"bind_throughput_ops_sec\":"<<jf(hrrU.bind_ops)<<",\"unbind_throughput_ops_sec\":"<<jf(hrrU.unbind_ops)<<",\"cleanup_sweep_ops_sec\":"<<jf(hrrU.cleanup_ops)<<",\"recovery_top1_rate_k8\":"<<jf(row(hrrU.rows,8).top1_rate)<<",\"recovery_top1_rate_k32\":"<<jf(row(hrrU.rows,32).top1_rate)<<",\"sweep\":";rows_json(o,hrrU.rows);o<<"},";
    o<<"\"bsc\":{\"bind_throughput_ops_sec\":"<<jf(bsc.bind_ops)<<",\"unbind_throughput_ops_sec\":"<<jf(bsc.unbind_ops)<<",\"cleanup_sweep_ops_sec\":"<<jf(bsc.cleanup_ops)<<",\"permute_ops_sec\":"<<jf(bsc.permute_ops)<<",\"recovery_top1_rate_k8\":"<<jf(row(bsc.rows,8).top1_rate)<<",\"recovery_top1_rate_k32\":"<<jf(row(bsc.rows,32).top1_rate)<<",\"sweep\":";rows_json(o,bsc.rows);o<<"}},";
    o<<"\"elapsed_ms\":"<<jf(elapsed)<<",\"throughput_ops_sec\":{\"hrr_bind\":"<<jf(hrrG.bind_ops)<<",\"bsc_bind\":"<<jf(bsc.bind_ops)<<"},";
    o<<"\"falsifiers_held\":[";bool first=true;auto held=[&](const char*n,bool ok){if(!ok){if(!first)o<<",";first=false;o<<"\""<<n<<"\"";}};held("HRR_FFT_REFERENCE",fft_ref);held("HRR_IDENTITY",hrr_identity);held("BSC_SELF_INVERSE",bsc_self);held("BSC_PERMUTE_INVERSE",perm_inverse);held("TOP1_RECOVERY_K8",top1k8);held("ORTHOGONAL_NOISE_FLOOR",ortho);held("CAPACITY_BOUND_K64",cap64);o<<"],";
    o<<"\"disposition\":\""<<(allpass?"PASS":"HOLD")<<"\"}";
    std::cout<<o.str()<<"\n";
    return allpass?0:2;
}