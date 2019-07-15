pruned=$(python prune_requirements.py $@)
echo $pruned
conda install --file $pruned
rm $pruned
