Output demo.gif
Set FontSize 14
Set Width 120
Set Height 36

Type "eval init my-project"
Enter
Sleep 1s
Type "cd my-project && eval run --dataset datasets/sample.jsonl --prompt prompts/qa.j2 --model gpt-4o-mini --scorer exact_match"
Enter
Sleep 3s
Type "eval show --run-id 1"
Enter
Sleep 1s
