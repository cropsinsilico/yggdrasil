pruned=$(python prune_requirements.py $1)
echo $pruned
conda install --file $pruned
rm $pruned
