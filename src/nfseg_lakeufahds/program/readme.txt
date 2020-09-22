Run the program by running nfseg.lakeufahds.exe. 

Input files: 
1. WaterBodiesFromTrey.dat: lakecell information from the lake shapefile provided by Trey; LakeID, row, col, AreaRatio (area of lake/area of model cell)
2. WaterBodiesFromVito.dat: lakecell information from the lake shapefile provided by Vito; LakeID, row, col, AreaRatio (area of lake/area of model cell)
3. WaterBodiesFromJohnGood.dat: lakecell information from the lake shapefile provided by John Good; Lake#, row, col, AreaRatio (area of lake/area of model cell), OBJECTID, LakeName

Output files:
1. WaterBodiesFromTrey.ufahds: area weighted simulated UFA heads beneath the lake for lakes provided by Trey; LakeID, UFA_Head_SP1, UFA_Head_SP2
2. WaterBodiesFromVito.ufahds: area weighted simulated UFA heads beneath the lake for lakes provided by Vito; LakeID, UFA_Head_SP1, UFA_Head_SP2
3. WaterBodiesFromJohnGood.ufahds: area weighted simulated UFA heads beneath the lake for lakes provided by John Good; Lake#, UFA_Head_SP1, UFA_Head_SP2
