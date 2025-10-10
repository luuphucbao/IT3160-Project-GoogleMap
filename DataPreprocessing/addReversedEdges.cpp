#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string edgesFile = "edges.txt";
    string newEdgesFile = "newEdges.txt";

    // ======= Đọc edges =======
    vector<tuple<ll,ll,double>> newEdges;
    ifstream finEdges(edgesFile);
    ll u, v; double w;
    while (finEdges >> u >> v >> w) {
        newEdges.push_back({u,v,w});
        newEdges.push_back({v,u,w});
    }
    finEdges.close();
    ofstream foutEdges(newEdgesFile);
    for (auto &[a, b, w] : newEdges)
        foutEdges << a << " " << b << " " << fixed << setprecision(4) << w << "\n";
    foutEdges.close();

    cout << "Hoan thanh. Ket qua luu tai:\n";
    cout << " - " << newEdgesFile << "\n";
    return 0;
}
